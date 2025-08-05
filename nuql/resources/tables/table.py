__all__ = ['Table']

from typing import Dict, Any, Optional

import nuql
from nuql import resources, types, api


class Table:
    def __init__(
            self,
            provider: 'nuql.Nuql',
            name: str,
            schema: Dict[str, 'types.FieldConfig'],
            indexes: 'resources.Indexes',
    ) -> None:
        """
        Main Table API for performing actions against a single table.

        :arg provider: Nuql instance.
        :arg name: Table name.
        :arg schema: Field schema.
        :arg indexes: Table indexes.
        """
        self.name = name
        self.provider = provider
        self.indexes = indexes
        self.fields = resources.create_field_map(schema, self, provider.fields)
        self.serialiser = resources.Serialiser(self)

    def query(
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
        query = api.Query(self.provider, self)
        return query.invoke_sync(
            key_condition=key_condition,
            filter_condition=filter_condition,
            index_name=index_name,
            limit=limit,
            scan_index_forward=scan_index_forward,
            exclusive_start_key=exclusive_start_key,
            consistent_read=consistent_read,
        )

    def get(self, key: Dict[str, Any], consistent_read: bool = False) -> Dict[str, Any]:
        """
        Retrieves a record from the table using the key.

        :arg key: Record key as a dict.
        :param consistent_read: Perform a consistent read.
        :return: Deserialised record dict.
        """
        get = api.Get(self.provider, self)
        return get.invoke_sync(key=key, consistent_read=consistent_read)

    def create(self, data: Dict[str, Any], condition: Optional['types.QueryWhere'] = None) -> Dict[str, Any]:
        """
        Create a new item on the table.

        :arg data: Data to create.
        :param condition: Optional condition expression dict.
        :return: New item dict.
        """
        create = api.Create(self.provider, self)
        return create.invoke_sync(data=data, condition=condition)

    def delete(
            self,
            key: Dict[str, Any],
            condition: Optional['types.QueryWhere'] = None,
    ) -> None:
        """
        Performs a delete operation for an item on the table.

        :arg key: Record key as a dict.
        :param condition: Condition expression as a dict.
        """
        delete = api.Delete(self.provider, self)
        return delete.invoke_sync(key=key, condition=condition)

    def update(
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
        update = api.UpdateItem(self.provider, self)
        return update.invoke_sync(data=data, condition=condition, shallow=shallow)

    def put_item(self, data: Dict[str, Any], condition: Optional['types.QueryWhere'] = None) -> Dict[str, Any]:
        """
        Perform a put operation against the table.

        :arg data: Data to put.
        :param condition: Optional condition expression dict.
        :return: New item dict.
        """
        put = api.PutItem(self.provider, self)
        return put.invoke_sync(data=data, condition=condition)

    def upsert(self, data: Dict[str, Any], shallow: bool = False) -> Dict[str, Any]:
        """
        Updates an item in the table if it exists, otherwise creates a new one.

        [NOTE]
        Conditions aren't allowed for this API to avoid ambiguous
        ConditionCheckFailedException (as this is a catch-all for any condition).

        :arg data: Data to upsert.
        :param shallow: Activates shallow update mode (so that whole nested items are updated at once).
        :return: New item dict.
        """
        upsert = api.Upsert(self.provider, self)
        return upsert.invoke_sync(data=data, shallow=shallow)
