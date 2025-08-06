__all__ = ['Delete']

from typing import Any, Dict, Optional

from boto3.dynamodb.types import TypeSerializer
from botocore.exceptions import ClientError

import nuql
from nuql import types, api, resources
from nuql.api import Boto3Adapter, Condition


class Delete(Boto3Adapter):
    def prepare_client_args(
            self,
            key: Dict[str, Any],
            condition: Dict[str, Any] | None = None,
            exclude_condition: bool = False,
            **kwargs,
    ) -> Dict[str, Any]:
        """
        Prepares the request args for a delete operation of an item on the table (client API).

        :arg key: Record key as a dict.
        :param condition: Condition expression as a dict.
        :param exclude_condition: Exclude condition from request (i.e. for BatchWrite).
        :param kwargs: Additional args to pass to the request.
        """
        serialised_data = self.table.serialiser.serialise('query', key)
        resources.validate_condition_dict(condition)
        condition = api.Condition(self.table, condition, 'ConditionExpression')

        # Marshall into the DynamoDB format
        serialiser = TypeSerializer()
        marshalled_data = {k: serialiser.serialize(v) for k, v in serialised_data.items()}

        args = {'Key': marshalled_data, **kwargs}

        if not exclude_condition:
            args.update(condition.client_args)

        return args

    def prepare_args(
            self,
            key: Dict[str, Any],
            condition: Dict[str, Any] | None = None,
            exclude_condition: bool = False,
            **kwargs,
    ) -> Dict[str, Any]:
        """
        Prepares the request args for a delete operation of an item on the table (resource API).

        :arg key: Record key as a dict.
        :param condition: Condition expression as a dict.
        :param exclude_condition: Exclude condition from request (i.e. for BatchWrite).
        :param kwargs: Additional args to pass to the request.
        """
        resources.validate_condition_dict(condition)
        condition_expression = Condition(
            table=self.table,
            condition=condition,
            condition_type='ConditionExpression'
        )
        args = {'Key': self.table.serialiser.serialise_key(key), **kwargs}

        if not exclude_condition:
            args.update(condition_expression.resource_args)

        return args

    def invoke_sync(
            self,
            key: Dict[str, Any],
            condition: Dict[str, Any] | None = None,
    ) -> None:
        """
        Performs a delete operation for an item on the table.

        :arg key: Record key as a dict.
        :param condition: Condition expression as a dict.
        """
        args = self.prepare_args(key=key, condition=condition)

        try:
            self.client.connection.table.delete_item(**args)
        except ClientError as exc:
            raise nuql.Boto3Error(exc, args)
