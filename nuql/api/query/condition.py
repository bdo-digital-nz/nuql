__all__ = ['Condition']

from typing import Dict, Any, Literal

from boto3.dynamodb.conditions import ComparisonCondition, Attr

import nuql
from nuql import resources
from . import condition_builder


class Condition:
    def __init__(
            self,
            table: 'resources.Table',
            condition: str | None = None,
            variables: Dict[str, Any] | None = None,
            condition_type: Literal['FilterExpression', 'ConditionExpression'] = 'FilterExpression',
    ) -> None:
        """
        Base condition builder helper to resolve queries.

        :arg table: Table instance.
        :param condition: Condition string.
        :param variables: Condition variables.
        :param condition_type: Condition type (FilterExpression or ConditionExpression).
        """
        if variables is None:
            variables = {}

        self.table = table
        self.variables = variables
        self.type = condition_type
        self.condition = None
        self.validator = resources.Validator()

        if condition:
            query = condition_builder.build_query(condition)
            self.condition = self.resolve(query['condition'])

    @property
    def args(self) -> Dict[str, Any]:
        args = {}
        if self.condition:
            args[self.type] = self.condition
        return args

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

            is_key = field_name in self.table.indexes.index_keys
            is_projected_to_key = any([x in self.table.indexes.index_keys for x in field.projected_from])

            # Validate that keys cannot be present in the query
            if (is_key or is_projected_to_key) and self.type == 'FilterExpression':
                raise nuql.NuqlError(
                    code='ConditionError',
                    message=f'Field \'{field_name}\' cannot be used in a condition query'
                )

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
