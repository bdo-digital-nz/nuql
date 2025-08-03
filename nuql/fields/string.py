__all__ = ['String']

from nuql.resources import FieldBase


class String(FieldBase):
    type = 'string'

    def serialise(self, value: str | None) -> str | None:
        """
        Serialises a string value.

        :arg value: Value.
        :return: Serialised value
        """
        return str(value) if value else None

    def deserialise(self, value: str | None) -> str | None:
        """
        Deserialises a string value.

        :arg value: String value.
        :return: String value.
        """
        return str(value) if value else None
