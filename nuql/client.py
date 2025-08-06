__all__ = ['Nuql']

from typing import List, Type

from boto3 import Session

from nuql import types, api
from . import Connection, exceptions
from .resources import Table, Indexes


class Nuql:
    def __init__(
            self,
            name: str,
            indexes: 'types.IndexesType',
            schema: 'types.SchemaConfig',
            boto3_session: Session | None = None,
            fields: List[Type['types.FieldType']] | None = None,
    ) -> None:
        """
        Nuql - a lightweight DynamoDB library for implementing
        the single table model pattern.

        :arg name: DynamoDB table name.
        :arg indexes: Table index definition.
        :arg schema: Table design.
        :param boto3_session: Boto3 Session instance.
        """
        if not isinstance(boto3_session, Session):
            boto3_session = Session()

        if fields is None:
            fields = []

        self.connection = Connection(name, boto3_session)
        self.fields = fields
        self.__schema = schema
        self.__indexes = Indexes(indexes)

    @property
    def indexes(self) -> Indexes:
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

    def get_table(self, name: str) -> Table:
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
        return Table(name=name, provider=self, schema=schema, indexes=self.indexes)
