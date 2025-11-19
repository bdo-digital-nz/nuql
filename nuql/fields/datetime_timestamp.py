__all__ = ['DatetimeTimestamp']

from datetime import datetime, UTC
from decimal import Decimal, InvalidOperation

import nuql
from nuql.resources import FieldBase


class DatetimeTimestamp(FieldBase):
    type = 'datetime_timestamp'

    def serialise(self, value: datetime | None) -> int | None:
        """
        Serialises a `datetime` to a timestamp.

        :arg value: `datetime` instance or `None`.
        :return: `int` or `None`.
        """
        if not isinstance(value, datetime):
            return None

        # Validate timezone-awareness
        if value.tzinfo is None:
            raise nuql.NuqlError(
                code='SerialisationError',
                message='Datetime value must be timezone-aware.'
            )

        return int(value.astimezone(UTC).timestamp())

    def deserialise(self, value: Decimal | None) -> datetime | None:
        """
        Deserialises a timestamp-like value to a `datetime`.

        Accepts Decimal, int, float, str, or None.
        Attempts conversion to Decimal first.

        :arg value: A value representing a timestamp, or None.
        :return: `datetime` instance or `None` if invalid.
        """

        if value is None:
            return None

        try:
            # For floats, avoid binary drift by converting via str()
            if isinstance(value, float):
                value = Decimal(str(value))
            else:
                value = Decimal(value)
        except (InvalidOperation, TypeError, ValueError):
            return None

        try:
            return datetime.fromtimestamp(int(value), UTC)
        except (ValueError, OSError, OverflowError, TypeError):
            return None
