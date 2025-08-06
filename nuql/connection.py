__all__ = ['Connection']

from boto3 import Session


class Connection:
    def __init__(self, table_name: str, boto3_session: Session, **connection_args) -> None:
        """
        Wrapper for the `boto3` DynamoDB resources/clients to be
        shared throughout the library.

        :arg table_name: DynamoDB table name.
        :arg boto3_session: Session instance.
        :param connection_args: Additional args to pass to the client/resource.
        """
        self.table_name = table_name
        self.session = boto3_session
        self.__connection_args = connection_args

        self.__resource = None
        self.__client = None
        self.__table = None

    @property
    def resource(self):
        """Creates a `boto3` DynamoDB resource if it doesn't exist."""
        if self.__resource is None:
            self.__resource = self.session.resource('dynamodb', **self.__connection_args)
        return self.__resource

    @property
    def client(self):
        """Creates a `boto3` DynamoDB client if it doesn't exist."""
        if self.__client is None:
            self.__client = self.session.client('dynamodb', **self.__connection_args)
        return self.__client

    @property
    def table(self):
        """Creates a `boto3` DynamoDB table if it doesn't exist."""
        if self.__table is None:
            self.__table = self.resource.Table(self.table_name)
        return self.__table
