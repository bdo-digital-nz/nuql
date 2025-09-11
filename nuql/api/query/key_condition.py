__all__ = ['KeyCondition']

from typing import Dict, Any, Tuple, Union

from boto3.dynamodb.conditions import Key, ConditionExpressionBuilder, ComparisonCondition

import nuql
from nuql import resources, types


KEY_OPERANDS = {
    # Equals
    'equals': 'eq',
    '=': 'eq',
    '==': 'eq',
    'eq': 'eq',

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
}


class KeyCondition:
    def __init__(self, table: 'resources.Table', condition: Dict[str, Any] | None = None, index_name: str = 'primary'):
        """
        DynamoDB key condition builder.

        :arg table: Table instance.
        :param condition: Condition dict.
        :param index_name: Optional index name.
        """
        if not isinstance(condition, (dict, type(None))):
            raise nuql.NuqlError(code='KeyConditionError', message='Key condition must be a dict or None.')

        if not condition:
            condition = {}

        self.index_name = index_name
        self.index = self._resolve_index(table, index_name)

        pk_field = table.fields[self.index['hash']]
        sk_field = table.fields.get(self.index.get('sort'))

        # Key fields that only contain fixed values should always be included
        if pk_field.auto_include_key_condition or pk_field.is_fixed and self.index['hash'] not in condition:
            condition[self.index['hash']] = None
        if sk_field.auto_include_key_condition or pk_field.is_fixed and self.index.get('sort') not in condition:
            condition[self.index.get('sort')] = None

        parsed_conditions = self.parse_conditions(table, condition, index_name)
        self.condition = self.build_condition_expression(table, parsed_conditions, index_name)

    @property
    def resource_args(self) -> Dict[str, Any]:
        """Query request args."""
        if self.condition is None:
            raise nuql.NuqlError(code='KeyConditionError', message='Key condition is empty.')

        args: Dict[str, Any] = {'KeyConditionExpression': self.condition}
        if self.index_name != 'primary':
            args['IndexName'] = self.index_name

        return args

    @property
    def client_args(self) -> Dict[str, Any]:
        """Boto3 client args for the condition."""
        if self.condition is None:
            raise nuql.NuqlError(code='KeyConditionError', message='Key condition is empty.')

        args = {}

        if self.index_name != 'primary':
            args['IndexName'] = self.index_name

        builder = ConditionExpressionBuilder()
        expression = builder.build_expression(self.condition, is_key_condition=True)

        args['KeyConditionExpression'] = getattr(expression, 'condition_expression')
        args['ExpressionAttributeNames'] = getattr(expression, 'attribute_name_placeholders')
        args['ExpressionAttributeValues'] = getattr(expression, 'attribute_value_placeholders')

        return args

    @staticmethod
    def extract_condition(key: str, value: Any) -> Tuple[str, Any]:
        """
        Parses and extracts the operand and value from the condition.

        :arg key: Condition key.
        :arg value: Condition value or dict.
        :return: Tuple containing the operand and value.
        """
        value_keys = list(value.keys()) if isinstance(value, dict) else []
        if isinstance(value, dict) and all([x.lower() in KEY_OPERANDS for x in value.keys()]):
            if len(value_keys) > 1:
                raise nuql.NuqlError(
                    code='KeyConditionError',
                    message=f'Multiple operators provided for the key \'{key}\' (' + ', '.join(value_keys) + ').'
                )

            condition_dict = next(iter(value.items()))

            operand = KEY_OPERANDS[condition_dict[0].lower()]
            condition_value = condition_dict[1]
        else:
            operand = 'eq'
            condition_value = value

        return operand, condition_value

    def parse_conditions(self, table: 'resources.Table', condition: Dict[str, Any], index_name: str) -> Dict[str, Any]:
        """
        Parse the condition dict handling projected fields.

        :arg table: Table instance.
        :arg condition: Condition dict.
        :arg index_name: Index name.
        :return: Parsed condition dict.
        """
        parsed_conditions = {}

        for key, value in condition.items():
            # Validate that the key exists
            if key not in table.fields:
                raise nuql.NuqlError(code='KeyConditionError', message=f'Field \'{key}\' is not defined in the schema.')

            field = table.fields[key]

            is_hash_key = key == self.index['hash']
            is_sort_key = key == self.index.get('sort')
            projects_to_hash = self.index['hash'] in field.projected_from
            projects_to_sort = self.index.get('sort') in field.projected_from

            # Resolve projected fields to their respective key(s)
            projected_keys = []
            if projects_to_hash:
                projected_keys.append(self.index['hash'])
            if projects_to_sort:
                projected_keys.append(self.index['sort'])

            # Validate that the key is available on the index
            if not is_hash_key and not is_sort_key and not projects_to_hash and not projects_to_sort:
                raise nuql.NuqlError(
                    code='KeyConditionError',
                    message=f'Field \'{key}\' cannot be used in a key condition on \'{index_name}\' index '
                            f'as it is not a hash/sort key and it doesn\'t project to the hash/sort key.'
                )

            operand, condition_value = self.extract_condition(key, value)

            # Directly set the key field where not projected
            if is_hash_key or is_sort_key:
                parsed_conditions[key] = [operand, condition_value]

            # Process projected field
            else:
                for key_name in projected_keys:
                    if key_name not in parsed_conditions:
                        parsed_conditions[key_name] = ['eq', {}]

                    parsed_conditions[key_name][1][key] = condition_value

                    # Allow a key with projections to have a greater_than or begins_with operator
                    # without disrupting the integrity of the condition
                    if parsed_conditions[key_name][0] != 'eq' and operand != 'eq':
                        raise nuql.NuqlError(
                            code='KeyConditionError',
                            message=f'Multiple non-equals operators provided for the key \'{key_name}\' '
                                    'will result in an ambiguous key condition.'
                        )

                    # The first non-equals operand becomes the winner
                    if operand != 'eq':
                        parsed_conditions[key_name][0] = operand

        if self.index['hash'] not in parsed_conditions:
            raise nuql.NuqlError(
                code='KeyConditionError',
                message=f'Hash key \'{self.index["hash"]}\' is required in the key condition '
                        f'but was not provided nor could be inferred from the schema.'
            )

        return parsed_conditions

    def build_condition_expression(
            self,
            table: 'resources.Table',
            parsed_conditions: Dict[str, Any],
            index_name: str
    ) -> ComparisonCondition:
        """
        Builds the final condition expression to be used in the query.

        :arg table: Table instance.
        :arg parsed_conditions: Parsed conditions dict.
        :arg index_name: Index name.
        :return: ComparisonCondition instance.
        """
        condition = None
        validator = resources.Validator()

        # Generate key condition
        for key, (operand, value) in parsed_conditions.items():

            field = table.fields[key]

            key_obj = Key(key)
            key_condition_args = set()

            # Special case for the between operator
            if operand == 'between':
                if len(value) != 2:
                    raise nuql.NuqlError(
                        code='KeyConditionError',
                        message=f'Between operator requires exactly two values for the key \'{key}\'.'
                    )
                key_condition_args.add(field(value[0], 'query', validator))
                key_condition_args.add(field(value[1], 'query', validator))

            # All other operators use a single value
            else:
                key_condition_args.add(field(value, 'query', validator))

            is_partial = key in validator.partial_keys

            # Disallow partial keys on hash keys
            if key == self.index['hash'] and is_partial:
                raise nuql.NuqlError(
                    code='KeyConditionError',
                    message=f'Partial key \'{key}\' cannot be used in a key condition on \'{index_name}\' '
                            f'index as it is the hash key for the index.'
                )

            # Partial sort key is allowed, but we must switch the operand to begins_with
            if is_partial and operand == 'eq':
                operand = 'begins_with'
            elif is_partial and operand != 'begins_with':
                raise nuql.NuqlError(
                    code='KeyConditionError',
                    message=f'Operator \'{operand}\' is not supported for the key \'{key}\' '
                            f'as it results in a partial key. Only \'begins_with\' is supported.'
                )

            key_condition = getattr(key_obj, operand)(*key_condition_args)

            if condition is None:
                condition = key_condition
            else:
                condition &= key_condition

        return condition

    @staticmethod
    def _resolve_index(
            table: 'resources.Table',
            index_name: str
    ) -> Union['types.PrimaryIndex', 'types.SecondaryIndex',]:
        """Resolves the index to query against"""
        if index_name == 'primary':
            return table.indexes.primary
        else:
            return table.indexes.get_index(index_name)
