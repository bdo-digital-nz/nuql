__all__ = ['Datetime']

from datetime import datetime, UTC

import nuql
from nuql.resources import FieldBase


class Datetime(FieldBase):
    type = 'datetime'
    date_format = '%Y-%m-%dT%H:%M:%S%z'

    def serialise(self, value: datetime | None) -> str | None:
        """
        Serialises a datetime value.

        :arg value: datetime instance or None.
        :return: String representation of the datetime instance.
        """
        if not isinstance(value, datetime):
            return None

        # Validate that the datetime is timezone-aware
        if not value.tzinfo:
            raise nuql.NuqlError(
                code='SerialisationError',
                message='Datetime value must be timezone-aware.'
            )

        return str(value.astimezone(UTC).strftime(self.date_format))

    def deserialise(self, value: str | None) -> datetime | None:
        """
        Deserialises a datetime value.

        :arg value: String representation of the datetime.
        :return: datetime instance or None.
        """
        if value is None:
            return None

        # Parse the datetime string
        try:
            dt = datetime.strptime(value, self.date_format)
            dt = dt.replace(tzinfo=UTC)
            return dt

        except (ValueError, TypeError):
            return None
