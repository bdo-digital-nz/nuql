__all__ = ['Delete']

from typing import Any, Dict, Optional

from botocore.exceptions import ClientError

import nuql
from nuql import types
from nuql.api import Boto3Adapter, Condition


class Delete(Boto3Adapter):
    def prepare_args(
            self,
            key: Dict[str, Any],
            condition: Optional['types.QueryWhere'] = None,
    ) -> Dict[str, Any]:
        """
        Prepares the request args for a delete operation of an item on the table.

        :arg key: Record key as a dict.
        :param condition: Condition expression as a dict.
        """
        condition_expression = Condition(
            table=self.table,
            condition=condition,
            condition_type='ConditionExpression'
        )
        return {'Key': self.table.serialiser.serialise_key(key), **condition_expression.args}

    def invoke_sync(
            self,
            key: Dict[str, Any],
            condition: Optional['types.QueryWhere'] = None,
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
