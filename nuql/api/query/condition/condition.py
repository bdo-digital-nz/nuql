__all__ = ['Condition']

from typing import Dict, Any

from boto3.dynamodb.conditions import ComparisonCondition, Attr

from nuql import resources
from . import builder


class Condition:
    def __init__(self, table: 'resources.Table', condition: str, variables: Dict[str, Any] | None = None) -> None:
        """
        Base condition builder helper to resolve queries.

        :arg table: Table instance.
        :arg condition: Condition string.
        :param variables: Condition variables.
        """
        if variables is None:
            variables = {}

        self.table = table
        self.variables = variables

        query = builder.build_query(condition)
        self.parsed_conditions = query['condition']
        self.condition = self.resolve(self.parsed_conditions)

    def resolve(self, part: Any) -> ComparisonCondition:
        """
        Recursively resolves condition parts.

        :arg part: Part to resolve.
        :return: ComparisonCondition instance.
        """
        if isinstance(part, dict) and part['type'] == 'condition':
            attr = Attr(part['field'])

            if part['value_type'] == 'function':
                expression = getattr(attr, part['operand'])()
            else:
                expression = getattr(attr, part['operand'])(part['value'])

            return expression

        elif isinstance(part, dict) and part['type'] == 'parentheses':
            condition = None
            last_operator = None

            for item in part['conditions']:
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

        raise ValueError('TODO invalid query')
