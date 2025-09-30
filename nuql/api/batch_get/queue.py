__all__ = ['BatchGetQueue']

from typing import List, Dict, Any

from boto3.dynamodb.types import TypeSerializer, TypeDeserializer

from nuql import resources


class BatchGetQueue:
    def __init__(self, table: 'resources.Table', keys: List[Dict[str, Any]], already_serialised: bool = False):
        """
        Queue helper for performing batch get operations.

        :arg table: Table instance.
        :arg keys: List of record keys to retrieve.
        :param already_serialised: If true, do not serialise the keys.
        """
        self.table = table
        self.index = self.table.indexes.primary
        self.db_table_name = self.table.provider.connection.table_name

        self._store = self.prepare(keys, already_serialised=already_serialised)

    @staticmethod
    def get_key_hash(key: Dict[str, Any]) -> str:
        """
        Simple hash function to make the store accessible by key.

        :arg key: Key dict.
        :return: Str hash of the key.
        """
        return ','.join([str(key[sorted_key]) for sorted_key in sorted(key.keys())])

    @property
    def result(self) -> Dict[str, Any]:
        return {
            'items': [x['item'] for x in self._store.values() if x['item'] is not None],
            'unprocessed_keys': [
                x['deserialised_key'] for x in self._store.values() if x['item'] is None
            ]
        }

    def prepare(self, keys: List[Dict[str, Any]], already_serialised: bool = False) -> Dict[str, Any]:
        """
        Prepare the initial queue.

        :arg keys: Full list of record keys.
        :param already_serialised: If true, do not serialise the keys.
        :return: Queue dict.
        """
        output = {}
        serialiser = TypeSerializer()

        primary_keys = [self.index['hash']]

        if self.index.get('sort'):
            primary_keys.append(self.index['sort'])

        for key in keys:
            if already_serialised:
                serialised_key = key
            else:
                serialised_key = self.table.serialiser.serialise_key(key)

            serialised_key = {k: v for k, v in serialised_key.items() if k in primary_keys}

            key_hash = self.get_key_hash(serialised_key)

            marshalled_key = {k: serialiser.serialize(v) for k, v in serialised_key.items()}

            output[key_hash] = {
                'key': marshalled_key,
                'item': None,
                'dispatched': False,
                'processed': False,
                'deserialised_key': key
            }

        return output

    def process_response(self, response: Dict[str, Any]) -> None:
        """
        Process the raw response from DynamoDB.

        :arg response: Response dict.
        """
        processed = response.get('Responses', {}).get(self.db_table_name, [])
        unprocessed = response.get('UnprocessedKeys', {}).get(self.db_table_name, {}).get('Keys', [])
        deserialiser = TypeDeserializer()

        # Handle successful keys
        for item in processed:
            item = {k: deserialiser.deserialize(v) for k, v in item.items()}
            record_type = item.get('nuql:type', self.table.name)
            table = self.table

            if record_type != table.name:
                table = self.table.provider.get_table(record_type)

            data = table.serialiser.deserialise(item)
            key_hash = self.get_key_hash(table.serialiser.serialise_key(data))

            self._store[key_hash]['item'] = data
            self._store[key_hash]['processed'] = True

        # Handle unprocessed keys (throttled)
        for key in unprocessed:
            data = self.table.serialiser.deserialise(key)
            key_hash = self.get_key_hash(data)

            # Reset the item
            self._store[key_hash]['item'] = None
            self._store[key_hash]['processed'] = False
            self._store[key_hash]['dispatched'] = False

    def get_batch(self, size: int = 100) -> Dict[str, Any] | None:
        """
        Get a batch of unprocessed keys.

        :param size: Max number of keys to return.
        :return: List of key dicts or None.
        """
        # Collect items not yet processed or dispatched
        items = [
            (key_hash, entry)
            for key_hash, entry in self._store.items()
            if not entry['processed'] and not entry['dispatched']
        ]
        selected = items[:size]

        if not selected:
            return None

        # Mark dispatched to avoid re-dispatching
        for key_hash, entry in selected:
            entry['dispatched'] = True

        batch_keys = [entry['key'] for _, entry in selected]
        return {self.db_table_name: {'Keys': batch_keys}}
