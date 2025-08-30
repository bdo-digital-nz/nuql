__all__ = ['BatchWrite']

from typing import Dict, Any, Literal

from botocore.exceptions import ClientError

import nuql
from nuql import resources, types, api


class BatchWrite:
    def __init__(self, client: 'nuql.Nuql') -> None:
        """
        Batch writer context manager.

        :arg client: Nuql instance.
        """
        self.client = client

        self._actions = {'put_item': [], 'delete_item': []}
        self._started = False

    def __enter__(self):
        """Enter the context manager."""
        self._actions = {'put_item': [], 'delete_item': []}
        self._started = True

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Dispatch batch write to DynamoDB."""
        try:
            with self.client.connection.table.batch_writer() as batch:
                for args in self._actions['put_item']:
                    batch.put_item(**args)

                for args in self._actions['delete_item']:
                    batch.delete_item(**args)

        except ClientError as exc:
            raise nuql.Boto3Error(exc, self._actions)

        self._started = False
        return False

    def _validate_started(self) -> None:
        """Validates that the context manager has been started."""
        if not self._started:
            raise nuql.NuqlError(
                code='BatchWriteError',
                message='Batch write context manager has not been started'
            )

    def put(
            self,
            table: 'resources.Table',
            data: Dict[str, Any],
            serialisation_type: Literal['create', 'update', 'write'] = 'write'
    ) -> None:
        """
        Create a new item on the table as part of a batch write.

        :arg table: Table instance.
        :arg data: Data to create.
        :param serialisation_type: Data serialisation type.
        """
        self._validate_started()

        if serialisation_type == 'create':
            create = api.Create(self.client, table)
            args = create.prepare_args(data=data, exclude_condition=True)

        elif serialisation_type == 'update':
            put_update = api.PutUpdate(self.client, table)
            args = put_update.prepare_args(data=data, exclude_condition=True)

        elif serialisation_type == 'write':
            put = api.PutItem(self.client, table)
            args = put.prepare_args(data=data, exclude_condition=True)

        else:
            raise nuql.NuqlError(
                code='BatchWriteError',
                message=f'Invalid serialisation type: {serialisation_type}'
            )

        self._actions['put_item'].append(args)

    def delete(
            self,
            table: 'resources.Table',
            key: Dict[str, Any],
    ) -> None:
        """
        Delete an item on the table as part of a batch write.

        :arg table: Table instance.
        :arg key: Item key.
        """
        self._validate_started()
        delete = api.Delete(self.client, table)
        args = delete.prepare_args(key=key, exclude_condition=True)
        self._actions['delete_item'].append(args)
