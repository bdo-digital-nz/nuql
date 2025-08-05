__all__ = ['UpdateExpressionBuilder']

from typing import Dict, Any

from .utils import flatten_dict, UpdateKeys, UpdateValues


class UpdateExpressionBuilder:
    def __init__(self, data: Dict[str, Any], shallow: bool = False) -> None:
        """
        DynamoDB update expression builder.

        :arg data: Serialised data to build expression from.
        :param shallow: Activates shallow update mode (so that whole nested items are updated at once).
        """
        if not shallow:
            data = flatten_dict(data)

        self.keys = UpdateKeys()
        self.update_expression = UpdateValues()

        for index, (key, value) in enumerate(data.items()):
            key = self.keys.add(key)
            self.update_expression.add(key, value)

    @property
    def args(self):
        """Returns the arguments for the boto3 API call."""
        return {
            'ExpressionAttributeNames': self.keys.expression_names,
            'ExpressionAttributeValues': self.update_expression.values,
            'UpdateExpression': 'SET ' + ', '.join(self.update_expression.expressions),
        }
