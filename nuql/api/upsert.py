__all__ = ['Upsert']

from typing import Any, Dict

import nuql
from nuql import api


class Upsert(api.Boto3Adapter):
    def invoke_sync(self, data: Dict[str, Any], shallow: bool = False) -> Dict[str, Any]:
        """
        Updates an item in the table if it exists, otherwise creates a new one.

        [NOTE]
        Conditions aren't allowed for this API to avoid ambiguous
        ConditionCheckFailedException (as this is a catch-all for any condition).

        :arg data: Data to upsert.
        :param shallow: Activates shallow update mode (so that whole nested items are updated at once).
        :return: New item dict.
        """
        try:
            update = api.UpdateItem(self.client, self.table)
            return update.invoke_sync(data=data, shallow=shallow)

        except nuql.Boto3Error as exc:
            # When condition failed the create API will be used instead.
            if exc.code == 'ConditionalCheckFailedException':
                create = api.Create(self.client, self.table)
                return create.invoke_sync(data=data)

            raise exc
