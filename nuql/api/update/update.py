__all__ = ['Update']

from typing import Any, Dict, Optional

from botocore.exceptions import ClientError

import nuql
from nuql import types, api


class Update(api.Boto3Adapter):
    def invoke_sync(
            self,
            data: Dict[str, Any],
            condition: Optional['types.QueryWhere'] = None,
            shallow: bool = False
    ) -> Dict[str, Any]:
        """
        Updates an item in the table.

        :arg data: Data to update.
        :param condition: Optional condition expression.
        :param shallow: Activates shallow update mode (so that whole nested items are updated at once).
        :return: New item dict.
        """
        # Serialise the data for update
        key = self.table.serialiser.serialise_key(data)
        serialised_data = {k: v for k, v in self.table.serialiser.serialise('update', data).items() if k not in key}

        # Generate the update expression
        update = api.UpdateExpressionBuilder(serialised_data, shallow=shallow)
        args = {'Key': key, **update.args, 'ReturnValues': 'ALL_NEW'}

        try:
            response = self.connection.table.update_item(**args)
        except ClientError as exc:
            raise nuql.Boto3Error(exc, args)

        return self.table.serialiser.deserialise(response['Attributes'])
