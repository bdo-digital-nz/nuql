__all__ = ['Boto3Adapter']

from typing import Any

import nuql
from nuql import resources


class Boto3Adapter:
    def __init__(self, client: 'nuql.Nuql', table: 'resources.Table'):
        """
        Wrapper around API actions against boto3.

        :arg client: Nuql instance.
        """
        self.client = client
        self.connection = client.connection
        self.table = table

    def invoke_sync(self, *args, **kwargs) -> Any:
        """Synchronously invokes boto3 API."""
        raise NotImplementedError('Synchronous API invocation has not been implemented for this method.')

    async def invoke_async(self, *args, **kwargs) -> Any:
        """Asynchronously invokes boto3 API."""
        raise NotImplementedError('Asynchronous API invocation has not been implemented for this method.')
