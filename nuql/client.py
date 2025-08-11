__all__ = ['Nuql']

from typing import List, Type, Dict, Any

from boto3 import Session

from nuql import types, api, resources
from . import Connection, exceptions


class Nuql:
    def __init__(
            self,
            name: str,
            indexes: List[Dict[str, Any]] | Dict[str, Any],
            schema: Dict[str, Any],
            session: Session | None = None,
            custom_fields: List[Type['types.FieldType']] | None = None,
            global_fields: Dict[str, Any] | None = None,
    ) -> None:
        """
        Nuql - a lightweight DynamoDB library for implementing
        the single table model pattern.

        :arg name: DynamoDB table name.
        :arg indexes: Table index definition.
        :arg schema: Table design.
        :param session: Boto3 Session instance.
        :param custom_fields: List of custom field types.
        :param global_fields: Additional field definitions to apply to all tables.
        """
        if not isinstance(session, Session):
            session = Session()

        if custom_fields is None:
            custom_fields = []

        # Insert global fields on to all tables
        if isinstance(global_fields, dict):
            for table_name in list(schema.keys()):
                schema[table_name].update(global_fields)

        self.connection = Connection(name, session)
        self.fields = custom_fields
        self.__schema = schema
        self.__indexes = resources.Indexes(indexes)

        resources.validate_schema(self.__schema, self.fields)

    @property
    def indexes(self) -> 'resources.Indexes':
        return self.__indexes

    @property
    def schema(self) -> 'types.SchemaConfig':
        return self.__schema

    def batch_write(self) -> 'api.BatchWrite':
        """
        Instantiates a `BatchWrite` object for performing batch writes to DynamoDB.

        :return: BatchWrite instance.
        """
        return api.BatchWrite(self)

    def transaction(self) -> 'api.Transaction':
        """
        Instantiates a `Transaction` object for performing transactions on a DynamoDB table.

        :return: Transaction instance.
        """
        return api.Transaction(self)

    def get_table(self, name: str) -> 'resources.Table':
        """
        Instantiates a `Table` object for the chosen table in the schema.

        :arg name: Table name (in schema) to instantiate.
        :return: Table instance.
        """
        if name not in self.__schema:
            raise exceptions.NuqlError(
                code='TableNotDefined',
                message=f'Table \'{name}\' is not defined in the schema.'
            )

        schema = self.__schema[name]
        return resources.Table(name=name, provider=self, schema=schema, indexes=self.indexes)
