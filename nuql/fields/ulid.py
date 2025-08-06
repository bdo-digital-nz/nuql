__all__ = ['Ulid']

from ulid import ULID

from nuql import resources


class Ulid(resources.FieldBase):
    type = 'ulid'

    def serialise(self, value: ULID | str | None) -> str | None:
        """
        Serialises a ULID value.

        :arg value: ULID, str or None.
        :return: str or None.
        """
        if isinstance(value, ULID):
            return str(value)
        if isinstance(value, str):
            try:
                return str(ULID(value.encode()))
            except ValueError:
                return None
        return None

    def deserialise(self, value: str | None) -> str | None:
        """
        Deserialises a ULID value.

        :arg value: str or None.
        :return: str or None.
        """
        if isinstance(value, str):
            try:
                return str(ULID(value.encode()))
            except ValueError:
                return None
        return None
