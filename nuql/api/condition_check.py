__all__ = ['ConditionCheck']

from typing import Dict, Any

from boto3.dynamodb.types import TypeSerializer

from nuql import types, api
from nuql.api import Boto3Adapter


class ConditionCheck(Boto3Adapter):
    def prepare_client_args(self, key: Dict[str, Any], condition: 'types.QueryWhere', **kwargs) -> Dict[str, Any]:
        """
        Prepare the request args for a condition check operation against the table (client API).

        :arg key: Record key as a dict.
        :arg condition: Condition expression.
        :param kwargs: Optional parameters to add to the request.
        :return: Client request args.
        """
        serialised_data = self.table.serialiser.serialise('query', key)
        condition = api.Condition(self.table, condition, 'ConditionExpression')

        # Marshall into the DynamoDB format
        serialiser = TypeSerializer()
        marshalled_data = {k: serialiser.serialize(v) for k, v in serialised_data.items()}

        args = {'Key': marshalled_data, **condition.client_args, **kwargs}

        # Serialise ExpressionAttributeValues into DynamoDB format
        if 'ExpressionAttributeValues' in args:
            for key, value in args['ExpressionAttributeValues'].items():
                args['ExpressionAttributeValues'][key] = serialiser.serialize(value)

        if 'ExpressionAttributeValues' in args and not args['ExpressionAttributeValues']:
            args.pop('ExpressionAttributeValues')

        return args
