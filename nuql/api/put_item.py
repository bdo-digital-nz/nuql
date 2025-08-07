__all__ = ['PutItem']

from typing import Any, Dict, Optional, Literal

from boto3.dynamodb.types import TypeSerializer
from botocore.exceptions import ClientError

import nuql
from nuql import types, api, resources
from nuql.api import Boto3Adapter


class PutItem(Boto3Adapter):
    serialisation_action: Literal['create', 'update', 'write'] = 'write'

    def prepare_client_args(
            self,
            data: Dict[str, Any],
            condition: Optional['types.QueryWhere'] = None,
            exclude_condition: bool = False,
            **kwargs,
    ) -> Dict[str, Any]:
        """
        Prepare the request args for a put operation against the table (client API).

        :arg data: Data to put.
        :param condition: Optional condition expression dict.
        :param exclude_condition: Exclude condition from request (i.e. for BatchWrite).
        :param kwargs: Additional args to pass to the request.
        :return: New item dict.
        """
        serialised_data = self.table.serialiser.serialise(self.serialisation_action, data)
        condition = api.Condition(self.table, condition, 'ConditionExpression')
        condition_args = condition.client_args

        # Marshall into the DynamoDB format
        serialiser = TypeSerializer()
        marshalled_data = {k: serialiser.serialize(v) for k, v in serialised_data.items()}

        # Implement ability to modify condition before the request
        self.on_condition(condition)

        # Serialise ExpressionAttributeValues into DynamoDB format
        if 'ExpressionAttributeValues' in condition_args:
            condition_args = {**condition_args}
            for k, v in condition_args['ExpressionAttributeValues'].items():
                condition_args['ExpressionAttributeValues'][k] = serialiser.serialize(v)

        args: Dict[str, Any] = {'Item': marshalled_data, **kwargs}

        if not exclude_condition:
            args.update(condition.client_args)

        if 'ExpressionAttributeValues' in args and not args['ExpressionAttributeValues']:
            args.pop('ExpressionAttributeValues')

        return args

    def prepare_args(
            self,
            data: Dict[str, Any],
            condition: Dict[str, Any] | None = None,
            exclude_condition: bool = False,
            **kwargs,
    ) -> Dict[str, Any]:
        """
        Prepare the request args for a put operation against the table (resource API).

        :arg data: Data to put.
        :param condition: Optional condition expression dict.
        :param exclude_condition: Exclude condition from request (i.e. for BatchWrite).
        :param kwargs: Additional args to pass to the request.
        :return: New item dict.
        """
        serialised_data = self.table.serialiser.serialise(self.serialisation_action, data)
        resources.validate_condition_dict(condition, required=False)
        condition = api.Condition(self.table, condition, 'ConditionExpression')

        # Implement ability to modify condition before the request
        self.on_condition(condition)

        args = {'Item': serialised_data, **kwargs}

        if not exclude_condition:
            args.update(condition.resource_args)

        return args

    def on_condition(self, condition: 'api.Condition') -> None:
        """
        Make changes to the condition expression before request.

        :arg condition: Condition instance.
        """
        pass

    def invoke_sync(self, data: Dict[str, Any], condition: Dict[str, Any] | None = None) -> Dict[str, Any]:
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

        return args['Item']
