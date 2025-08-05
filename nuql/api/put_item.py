__all__ = ['PutItem']

from typing import Any, Dict, Optional, Literal

from boto3.dynamodb.types import TypeSerializer
from botocore.exceptions import ClientError

import nuql
from nuql import types, api
from nuql.api import Boto3Adapter


class PutItem(Boto3Adapter):
    serialisation_action: Literal['create', 'update', 'write'] = 'write'

    def prepare_client_args(
            self,
            data: Dict[str, Any],
            condition: Optional['types.QueryWhere'] = None
    ) -> Dict[str, Any]:
        """
        Prepare the request args for a put operation against the table (client API).

        :arg data: Data to put.
        :param condition: Optional condition expression dict.
        :return: New item dict.
        """
        serialised_data = self.table.serialiser.serialise(self.serialisation_action, data)
        condition = api.Condition(self.table, condition, 'ConditionExpression')

        # Marshall into the DynamoDB format
        serialiser = TypeSerializer()
        marshalled_data = {k: serialiser.serialize(v) for k, v in serialised_data.items()}

        # Implement ability to modify condition before the request
        self.on_condition(condition)

        return {'Item': marshalled_data, **condition.client_args, 'ReturnValues': 'NONE'}

    def prepare_args(self, data: Dict[str, Any], condition: Optional['types.QueryWhere'] = None) -> Dict[str, Any]:
        """
        Prepare the request args for a put operation against the table (resource API).

        :arg data: Data to put.
        :param condition: Optional condition expression dict.
        :return: New item dict.
        """
        serialised_data = self.table.serialiser.serialise(self.serialisation_action, data)
        condition = api.Condition(self.table, condition, 'ConditionExpression')

        # Implement ability to modify condition before the request
        self.on_condition(condition)

        return {'Item': serialised_data, **condition.resource_args, 'ReturnValues': 'NONE'}

    def on_condition(self, condition: 'api.Condition') -> None:
        """
        Make changes to the condition expression before request.

        :arg condition: Condition instance.
        """
        pass

    def invoke_sync(self, data: Dict[str, Any], condition: Optional['types.QueryWhere'] = None) -> Dict[str, Any]:
        """
        Perform a put operation against the table.

        :arg data: Data to put.
        :param condition: Optional condition expression dict.
        :return: New item dict.
        """
        args = self.prepare_args(data=data, condition=condition)

        try:
            self.connection.table.put_item(**args)
        except ClientError as exc:
            raise nuql.Boto3Error(exc, args)

        return self.table.serialiser.deserialise(args['Item'])
