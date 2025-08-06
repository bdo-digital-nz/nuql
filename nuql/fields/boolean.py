__all__ = ['Boolean']

from nuql.resources import FieldBase


class Boolean(FieldBase):
    type = 'boolean'

    def serialise(self, value: bool | None) -> bool | None:
        """
        Serialises a boolean value (type checker).

        :arg value: Boolean value.
        :return: Boolean value.
        """
        if isinstance(value, bool):
            return value
        return None

    def deserialise(self, value: bool | None) -> bool | None:
        """
        Deserialises a boolean value (type checker).

        :arg value: Boolean value.
        :return: Boolean value.
        """
        if isinstance(value, bool):
            return value
        return None
