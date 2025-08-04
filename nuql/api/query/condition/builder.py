__all__ = ['build_query']

from typing import Dict, Any, List

from pyparsing import Word, alphas, alphanums, Regex, Group, Forward, oneOf, infixNotation, opAssoc, QuotedString, \
    pyparsing_common, ParseException

import nuql


ATTR_OPERATORS = {
    # Equals
    'equals': 'eq',
    '=': 'eq',
    '==': 'eq',
    'eq': 'eq',
    'is': 'eq',

    # Not equals
    'not_equals': 'ne',
    '!=': 'ne',
    '<>': 'ne',
    'ne': 'ne',
    'is_not': 'ne',

    # Less than
    'less_than': 'lt',
    '<': 'lt',
    'lt': 'lt',

    # Less than or equal to
    'less_than_or_equals': 'lte',
    'less_than_equals': 'lte',
    '<=': 'lte',
    'lte': 'lte',

    # Greater than
    'greater_than': 'gt',
    '>': 'gt',
    'gt': 'gt',

    # Greater than or equal to
    'greater_than_or_equals': 'gte',
    'greater_than_equals': 'gte',
    '>=': 'gte',
    'gte': 'gte',

    # Special
    'begins_with': 'begins_with',
    'between': 'between',
    'attribute_type': 'attribute_type',
    'contains': 'contains',
    'match': 'contains',
    'attribute_exists': 'exists',
    'attribute_not_exists': 'not_exists',
    'is_in': 'is_in',
    'in': 'is_in',
}


field = Word(alphas + '_' + alphanums + '.').set_results_name('field')

operand = oneOf('''
    = == equals eq is
    != <> not_equals ne is_not
    < less_than lt
    <= less_than_equals less_than_or_equals lte
    > greater_than gt
    >= greater_than_equals greater_than_or_equals gte
    contains match
    begins_with
    between
    is_in in
''', caseless=True).set_results_name('operand')

func = oneOf('attribute_exists attribute_not_exists', caseless=True).set_results_name('func')

variable = Regex(r'\$\{[^}]*\}').set_results_name('variable')
quoted_string = (QuotedString('"', unquote_results=False).set_results_name('string') |
                 QuotedString("'", unquote_results=False).set_results_name('string'))
integer = pyparsing_common.integer.set_results_name('integer')
number = pyparsing_common.number.set_results_name('number')
boolean = oneOf('true false', caseless=True)

value = variable | quoted_string | number | integer | boolean

condition_group = Group(field + operand + value)
function_group = Group(func + '(' + field + ')')

expression = Forward()
expression <<= infixNotation(
    (condition_group | function_group), [
        (oneOf('and', caseless=True), 2, opAssoc.LEFT),
        (oneOf('or', caseless=True), 2, opAssoc.LEFT),
    ]
)


def build_query(query: str | None) -> Dict[str, Any]:
    """
    Build query dict from string.

    :arg query: Query string.
    :return: Query dict payload.
    """
    try:
        parsed = expression.parse_string(query)[0].as_list()
    except ParseException as e:
        raise nuql.NuqlError(
            code='ConditionParsingError',
            message=f'Unable to parse condition: {e}'
        )

    variables = []

    def recursive_unpack(part: Any, captured_variables: List[str]) -> Dict[str, Any]:
        if is_condition(part):
            value_is_variable = isinstance(part[2], str) and part[2].startswith('${') and part[2].endswith('}')
            if value_is_variable:
                captured_variables.append(part[2].replace('${', '').replace('}', ''))
            return {
                'type': 'condition',
                'field': part[0],
                'operand': ATTR_OPERATORS[part[1].lower()],
                **parse_value(part[2])
            }

        elif is_function(part):
            return {
                'type': 'function',
                'field': part[2],
                'function': ATTR_OPERATORS[part[0].lower()]
            }

        elif is_logical_operator(part):
            return {'type': 'logical_operator', 'operator': part}

        else:
            return {
                'type': 'parentheses',
                'conditions': [recursive_unpack(item, captured_variables) for item in part]
            }

    result = recursive_unpack(parsed, variables)

    return {'condition': result, 'variables': list(set(variables))}


def is_condition(part: Any):
    return isinstance(part, list) and all(isinstance(item, str) for item in part[:-1]) and len(part) == 3


def is_function(part: Any):
    return isinstance(part, list) and all(isinstance(item, str) for item in part) and len(part) == 4


def is_logical_operator(part: Any):
    return isinstance(part, str) and part in ['and', 'AND', 'or', 'OR']


def parse_value(var: str) -> Dict[str, Any]:
    """
    Parses provided variable.

    :arg var: Variable to parse.
    :return: Condition result keys.
    """
    # Parse variable
    try:
        var = variable.parse_string(var)
        return {'value_type': 'variable', 'variable': var.variable.replace('${', '').replace('}', '')}
    except (ParseException, AttributeError):
        pass

    # Parse quoted string
    try:
        var = quoted_string.parse_string(var)
        return {
            'value_type': 'string',
            'value': var.string.lstrip('"').rstrip('"')
            if var.string.startswith('"')
            else var.string.lstrip("'").rstrip("'")
        }
    except (ParseException, AttributeError):
        pass

    # Parse integer type
    if isinstance(var, int):
        return {'value_type': 'integer', 'value': var}

    # Parse number
    if isinstance(var, float):
        return {'value_type': 'number', 'value': var}

    if isinstance(var, str) and var.lower() == 'true':
        return {'value_type': 'boolean', 'value': True}

    if isinstance(var, str) and var.lower() == 'false':
        return {'value_type': 'boolean', 'value': False}

    raise nuql.NuqlError(code='ConditionParsingError', message=f'Unable to parse variable \'{var}\' in condition.')
