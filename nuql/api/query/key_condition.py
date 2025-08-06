__all__ = ['KeyCondition']

from typing import Dict, Any

from boto3.dynamodb.conditions import Key, ConditionExpressionBuilder

import nuql
from nuql import resources


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

        if index_name == 'primary':
            self.index = table.indexes.primary
        else:
            self.index = table.indexes.get_index(index_name)

        if self.index['hash'] not in condition:
            condition[self.index['hash']] = None

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

            # Validate that the key is available on the index
            if not any([is_hash_key, is_sort_key, projects_to_hash, projects_to_sort]):
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
                key_name = self.index['hash'] if is_hash_key else self.index['sort']

                if key_name not in parsed_conditions:
                    parsed_conditions[key_name] = ['eq', {}]

                if parsed_conditions[key_name][0] != 'eq' and operand != 'eq':
                    raise nuql.NuqlError(
                        code='KeyConditionError',
                        message=f'Multiple non-equals operators provided for the key \'{key_name}\' '
                                'will result in an ambiguous key condition.'
                    )

                if operand != 'eq':
                    parsed_conditions[key_name][0] = operand

                parsed_conditions[key_name][1][key] = condition_value

        self.condition = None
        validator = resources.Validator()

        # Generate key condition
        for key, (operand, value) in parsed_conditions.items():
            field = table.fields[key]
            key_obj = Key(key)

            if operand == 'between':
                if len(value) != 2:
                    raise nuql.NuqlError(
                        code='KeyConditionError',
                        message=f'Between operator requires exactly two values for the key \'{key}\'.'
                    )
                serialised_value = (field(value[0], 'query', validator), field(value[1], 'query', validator))
                key_condition = getattr(key_obj, operand)(*serialised_value)
            else:
                serialised_value = field(value, 'query', validator)
                key_condition = getattr(key_obj, operand)(serialised_value)

            if self.condition is None:
                self.condition = key_condition
            else:
                self.condition &= key_condition

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
    def extract_condition(key: str, value: Any) -> (str, Any):
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
