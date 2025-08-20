__all__ = ['Ulid']

from typing import Any

import nuql
from nuql import resources


class Ulid(resources.FieldBase):
    type = 'ulid'

    def serialise(self, value: Any) -> str | None:
        """
        Serialises a ULID value.

        :arg value: ULID, str or None.
        :return: str or None.
        """
        try:
            import ulid
        except ImportError:
            raise nuql.NuqlError(
                code='DependencyError',
                message='The "python-ulid" package is required to use the ULID field.'
            ) from None

        if isinstance(value, ulid.ULID):
            return str(value)
        if isinstance(value, str):
            try:
                return str(ulid.ULID.from_str(value))
            except ValueError:
                return None
        return None

    def deserialise(self, value: str | None) -> str | None:
        """
        Deserialises a ULID value.

        :arg value: str or None.
        :return: str or None.
        """
        try:
            import ulid
        except ImportError:
            raise nuql.NuqlError(
                code='DependencyError',
                message='The "python-ulid" package is required to use the ULID field.'
            ) from None

        if isinstance(value, str):
            try:
                return str(ulid.ULID.from_str(value))
            except ValueError:
                return None
        return None
