__all__ = ['BatchGet']

from typing import Any, List, Dict

from botocore.exceptions import ClientError

import nuql
from nuql import api
from nuql.api import Boto3Adapter


class BatchGet(Boto3Adapter):
    def invoke_sync(self, keys: List[Dict[str, Any]], already_serialised: bool = False) -> Dict[str, Any]:
        """
        Performs a batch get operation against the table.

        :arg keys: Keys to get.
        :param already_serialised: If True, the keys are already serialised.
        :return: Batch get result.
        """
        queue = api.BatchGetQueue(self.table, keys, already_serialised=already_serialised)
        fulfilled = False

        # Loop through until all keys have been processed
        while not fulfilled:
            batch = queue.get_batch()

            if batch is None:
                fulfilled = True
                continue

            args = {'RequestItems': batch}

            try:
                response = self.client.connection.client.batch_get_item(**args)
                queue.process_response(response)

            except ClientError as exc:
                raise nuql.Boto3Error(exc, args)

        return queue.result
