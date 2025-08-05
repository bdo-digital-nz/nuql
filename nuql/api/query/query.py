__all__ = ['Query']

from typing import Any, Dict, Optional

from botocore.exceptions import ClientError

import nuql
from nuql import types, api


class Query(api.Boto3Adapter):
    def invoke_sync(
            self,
            key_condition: Dict[str, Any] | None = None,
            filter_condition: Optional['types.QueryWhere'] = None,
            index_name: str = 'primary',
            limit: int | None = None,
            scan_index_forward: bool = True,
            exclusive_start_key: Dict[str, Any] | None = None,
            consistent_read: bool = False,
    ) -> 'types.QueryResult':
        """
        Synchronously invokes a query against the table.

        :param key_condition: Key condition expression as a dict.
        :param filter_condition: Filter condition expression as a dict.
        :param index_name: Index to perform query against.
        :param limit: Number of items to retrieve.
        :param scan_index_forward: Direction of scan.
        :param exclusive_start_key: Exclusive start key.
        :param consistent_read: Perform query as a consistent read.
        :return: Query result.
        """
        # Key condition is parsed from a dict and validated
        key_condition = api.KeyCondition(self.table, key_condition, index_name)

        # Filter condition is parsed from a string and validated
        filter_condition = api.Condition(
            table=self.table,
            condition=filter_condition,
            condition_type='FilterExpression'
        )

        args: Dict[str, Any] = {
            **key_condition.args,
            **filter_condition.args,
            'ScanIndexForward': scan_index_forward,
            'ConsistentRead': consistent_read,
        }

        data = []
        last_evaluated_key = exclusive_start_key
        fulfilled = False

        while not fulfilled:
            # Subtract processed records from limit
            if isinstance(limit, int):
                args['Limit'] = limit - len(data)

            # Break when limit is reached
            if 'Limit' in args and args['Limit'] == 0:
                break

            # Pagination is achieved by using LEK as exclusive start key
            if last_evaluated_key:
                args['ExclusiveStartKey'] = last_evaluated_key

            try:
                response = self.connection.table.query(**args)
            except ClientError as exc:
                raise nuql.Boto3Error(exc, args)

            data.extend(response.get('Items', []))
            last_evaluated_key = response.get('LastEvaluatedKey')

            if not last_evaluated_key:
                fulfilled = True

        return {
            'items': [self.table.serialiser.deserialise(item) for item in data],
            'last_evaluated_key': last_evaluated_key,
        }
