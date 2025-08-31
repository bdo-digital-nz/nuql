__all__ = ['SchemaProvider']

from typing import List, Dict, Any

import nuql
from nuql import resources


class SchemaProvider:
    def __init__(self, provider: 'nuql.Nuql', schema: Dict[str, Any]) -> None:
        """
        Schema and serialisation/deserialisation helper.

        :arg provider: `Nuql` instance.
        :arg schema: Schema dict.
        """
        resources.validate_schema(schema)
        self.tables = schema

    def get_field_map(self, tables: List[str] | None = None) -> Dict[str, Any]:
        """
        Generates a field map for one or more tables.

        :param tables: List of table names.
        :return: Field mapping dict.
        """
        if not tables:
            tables = list(self.tables.keys())

        field_map = {}

        for table in tables:
            table_schema = self.tables[table]
            for field_name, field_schema in table_schema.items():
                field_map[field_name] = field_schema

        return field_map
