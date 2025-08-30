__all__ = ['Condition']

from typing import Dict, Any, Literal, Optional

from boto3.dynamodb.conditions import ComparisonCondition, Attr, ConditionExpressionBuilder

import nuql
from nuql import resources, types
from . import condition_builder


class Condition:
    def __init__(
            self,
            table: 'resources.Table',
            condition: str | Dict[str, Any] | None = None,
            condition_type: Literal['FilterExpression', 'ConditionExpression'] = 'FilterExpression',
    ) -> None:
        """
        Base condition builder helper to resolve queries.

        :arg table: Table instance.
        :param condition: Condition dict.
        :param condition_type: Condition type (FilterExpression or ConditionExpression).
        """
        # Initialise the condition even when it is a string
        if isinstance(condition, str):
            condition = {'where': condition, 'variables': {}}

        self.table = table
        self.variables = condition['variables'] if condition and condition.get('variables') else {}
        self.type = condition_type
        self.condition = None
        self.validator = resources.Validator()

        if condition:
            query = condition_builder.build_query(condition['where'])
            self.condition = self.resolve(query['condition'])

    @property
    def resource_args(self) -> Dict[str, Any]:
        """Boto3 resource args for the condition."""
        args = {}
        if self.condition:
            args[self.type] = self.condition
        return args

    @property
    def client_args(self) -> Dict[str, Any]:
        """Boto3 client args for the condition."""
        if not self.condition:
            return {}

        builder = ConditionExpressionBuilder()
        expression = builder.build_expression(self.condition, is_key_condition=False)

        expression_string = getattr(expression, 'condition_expression')
        attribute_name_placeholders = getattr(expression, 'attribute_name_placeholders')
        attribute_value_placeholders = getattr(expression, 'attribute_value_placeholders')

        return {
            'ConditionExpression': expression_string,
            'ExpressionAttributeNames': attribute_name_placeholders,
            'ExpressionAttributeValues': attribute_value_placeholders,
        }

    def append(self, condition: str) -> None:
        """
        Append a condition to the current condition.

        :arg condition: Condition string.
        """
        if isinstance(condition, str):
            condition = condition_builder.build_query(condition)['condition']
        condition = self.resolve(condition)
        if self.condition:
            self.condition &= condition
        else:
            self.condition = condition

    def resolve(self, part: Any) -> ComparisonCondition:
        """
        Recursively resolves condition parts.

        :arg part: Part to resolve.
        :return: ComparisonCondition instance.
        """
        # Direct condition/function handling
        if isinstance(part, dict) and part['type'] in ['condition', 'function']:
            attr = Attr(part['field'])
            field_name = part['field']
            field = self.table.fields.get(field_name)

            # Functions are called differently
            if part['type'] == 'function':
                expression = getattr(attr, part['function'])()

            # Handle basic conditions
            else:
                if not field:
                    raise nuql.NuqlError(
                        code='ConditionError',
                        message=f'Field \'{field_name}\' is not defined in the schema'
                    )

                # Variables provided outside of the query string
                if part['value_type'] == 'variable':
                    if part['variable'] not in self.variables:
                        raise nuql.NuqlError(
                            code='ConditionError',
                            message=f'Variable \'{part["variable"]}\' is not defined in the condition'
                        )
                    value = self.variables[part['variable']]

                # Rudimentary values passed in the query string
                else:
                    value = part['value']

                # Value is serialised for a query
                expression = getattr(attr, part['operand'])(field(value, action='query', validator=self.validator))

            return expression

        # Handle grouped conditions
        elif isinstance(part, dict) and part['type'] == 'parentheses':
            condition = None
            last_operator = None

            for item in part['conditions']:
                # Logical operator is stored outside of the loop so that it is used
                if isinstance(item, dict) and item['type'] == 'logical_operator':
                    last_operator = item['operator']

                else:
                    expression = self.resolve(item)

                    if last_operator is None:
                        condition = expression
                    elif last_operator == 'and':
                        condition &= expression
                    elif last_operator == 'or':
                        condition |= expression

            return condition

        raise nuql.NuqlError(
            code='ConditionParsingError',
            message='Unresolvable condition part was provided',
            part=part
        )
