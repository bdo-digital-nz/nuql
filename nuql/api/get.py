__all__ = ['Get']

from typing import Any, Dict

from botocore.exceptions import ClientError

import nuql
from nuql.api import Boto3Adapter


class Get(Boto3Adapter):
    def invoke_sync(self, key: Dict[str, Any], consistent_read: bool = False) -> Dict[str, Any]:
        """
        Retrieves a record from the table using the key.

        :arg key: Record key as a dict.
        :param consistent_read: Perform a consistent read.
        :return: Deserialised record dict.
        """
        args = {'Key': self.table.serialiser.serialise_key(key), 'ConsistentRead': consistent_read}

        try:
            response = self.client.connection.table.get_item(**args)
        except ClientError as exc:
            raise nuql.Boto3Error(exc, args)

        if 'Item' not in response:
            raise nuql.ItemNotFound(args['Key'])

        return self.table.serialiser.deserialise(response['Item'])
