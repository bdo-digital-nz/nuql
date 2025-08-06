__all__ = ['Transaction']

from typing import Dict, Any, Optional, Literal

from botocore.exceptions import ClientError

import nuql
from nuql import types, api, resources


# Maximum number of actions in a transaction
MAX_TRANSACTION_ACTIONS = 100


class Transaction:
    def __init__(self, client: 'nuql.Nuql') -> None:
        """
        Context manager for executing DynamoDB transactions.

        :arg client: Nuql instance.
        """
        self.client = client

        self._actions = []
        self._started = False

    def __enter__(self):
        """Enter the context manager."""
        self._actions = []
        self._started = True

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Dispatch the transaction to DynamoDB."""
        if not self._actions:
            raise nuql.NuqlError(
                code='TransactionError',
                message='Transaction has no actions'
            )

        args = {'TransactItems': self._actions}

        try:
            self.client.connection.client.transact_write_items(**args)
        except ClientError as exc:
            raise nuql.Boto3Error(exc, args)

        self._started = False
        return False

    def _validate(self) -> None:
        """Validates that the context manager has been started and maximum has not been exceeded."""
        if not self._started:
            raise nuql.NuqlError(
                code='TransactionError',
                message='Transaction context manager has not been started'
            )
        if len(self._actions) > MAX_TRANSACTION_ACTIONS:
            raise nuql.NuqlError(
                code='TransactionError',
                message=f'Maximum number of actions exceeded in transaction (limit {MAX_TRANSACTION_ACTIONS})'
            )

    def create(
            self,
            table: 'resources.Table',
            data: Dict[str, Any],
            condition: Optional['types.QueryWhere'] = None,
    ) -> None:
        """
        Create a new item on a table as part of a transaction.

        :arg table: Table instance.
        :arg data: Data to create.
        :param condition: Optional condition expression dict.
        """
        self._validate()

        create = api.Create(self.client, table)
        args = create.prepare_client_args(data=data, condition=condition)

        self._actions.append({'Put': {'TableName': self.client.connection.table_name, **args}})

    def update(
            self,
            table: 'resources.Table',
            data: Dict[str, Any],
            condition: Optional['types.QueryWhere'] = None,
            shallow: bool = False,
    ) -> None:
        """
        Update an item on a table as part of a transaction.

        :arg table: Table instance.
        :arg data: Data to update.
        :param condition: Optional condition expression dict.
        :param shallow: Activates shallow update mode (so that whole nested items are updated at once).
        """
        self._validate()

        update = api.UpdateItem(self.client, table)
        args = update.prepare_client_args(data=data, condition=condition, shallow=shallow)

        self._actions.append({'Update': {'TableName': self.client.connection.table_name, **args}})

    def delete(
            self,
            table: 'resources.Table',
            key: Dict[str, Any],
            condition: Optional['types.QueryWhere'] = None,
    ) -> None:
        """
        Delete an item on a table as part of a transaction.

        :arg table: Table instance.
        :arg key: Record key as a dict.
        :param condition: Optional condition expression dict.
        """
        self._validate()

        delete = api.Delete(self.client, table)
        args = delete.prepare_client_args(key=key, condition=condition)

        self._actions.append({'Delete': {'TableName': self.client.connection.table_name, **args}})

    def condition_check(
            self,
            table: 'resources.Table',
            key: Dict[str, Any],
            condition: 'types.QueryWhere',
    ) -> None:
        """
        Perform a condition check on an item as part of a transaction.

        :arg table: Table instance.
        :arg key: Record key as a dict.
        :arg condition: Condition expression dict.
        """
        self._validate()

        condition_check = api.ConditionCheck(self.client, table)
        args = condition_check.prepare_client_args(key=key, condition=condition)

        self._actions.append({'ConditionCheck': {'TableName': self.client.connection.table_name, **args}})
