__all__ = ['Table']

from typing import Dict

import nuql
from nuql import resources, types


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
