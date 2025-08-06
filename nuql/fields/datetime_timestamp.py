__all__ = ['DatetimeTimestamp']

from datetime import datetime, UTC
from decimal import Decimal

import nuql
from nuql.resources import FieldBase


class DatetimeTimestamp(FieldBase):
    type = 'datetime_timestamp'

    def serialise(self, value: datetime | None) -> int | None:
        """
        Serialises a datetime to a timestamp.

        :arg value: datetime instance or None.
        :return: int or None.
        """
        if not isinstance(value, datetime):
            return None

        # Validate timezone-awareness
        if value.tzinfo is None:
            raise nuql.NuqlError(
                code='SerialisationError',
                message='Datetime value must be timezone-aware.'
            )

        return int(value.astimezone(UTC).timestamp() * 1000)

    def deserialise(self, value: Decimal | None) -> datetime | None:
        """
        Deserialises a timestamp to a datetime.

        :arg value: Decimal instance or None.
        :return: datetime instance or None.
        """
        if not isinstance(value, Decimal):
            return None

        try:
            return datetime.fromtimestamp(int(value) / 1000, UTC)
        except (ValueError, TypeError):
            return None
