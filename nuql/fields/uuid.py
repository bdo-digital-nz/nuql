__all__ = ['Uuid']

from uuid import UUID

from nuql import resources


class Uuid(resources.FieldBase):
    type = 'uuid'

    def serialise(self, value: UUID | str | None) -> str | None:
        """
        Serialises a UUID value.

        :arg value: UUID, str or None.
        :return: str or None.
        """
        if isinstance(value, UUID):
            return str(value)

        if isinstance(value, str):
            try:
                return str(UUID(value))
            except ValueError:
                return None

        return None

    def deserialise(self, value: str | None) -> str | None:
        """
        Deserialises a UUID value (only to string).

        :arg value: str or None.
        :return: str or None.
        """
        if isinstance(value, str):
            try:
                return str(UUID(value))
            except ValueError:
                return None
        return None
