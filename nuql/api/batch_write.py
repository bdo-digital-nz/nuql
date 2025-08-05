import nuql


class BatchWrite:
    def __init__(self, client: 'nuql.Nuql') -> None:
        """
        Batch writer context manager.

        :arg client: Nuql instance.
        """
        self.client = client

        self._actions = []
        self._started = False

    def __enter__(self):
        """Enter the context manager."""
        self._actions = []
        self._started = True

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Dispatch batch write to DynamoDB."""
        with self.client.connection.table.batch_writer() as batch:
            pass
