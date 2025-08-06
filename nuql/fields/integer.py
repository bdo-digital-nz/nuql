__all__ = ['Integer']

from decimal import Decimal
from typing import Any

from nuql.api import Incrementor
from nuql import resources, types


class Integer(resources.FieldBase):
    type = 'int'

    def serialise(self, value: int | Incrementor | None) -> Decimal | Incrementor | None:
        """
        Serialises an integer value.

        :arg value: Value as int, Incrementor or None.
        :return: Value as Decimal, Incrementor or None.
        """
        if not isinstance(value, (int, Incrementor)):
            return None
        if isinstance(value, Incrementor):
            return value
        return Decimal(str(value))

    def deserialise(self, value: Decimal | None) -> int | None:
        """
        Deserialises an integer value.

        :arg value: Value as Decimal or None.
        :return: Value as int or None.
        """
        if not isinstance(value, Decimal):
            return None
        return int(value)

    def internal_validation(self, value: Any, action: 'types.SerialisationType', validator: 'resources.Validator'):
        """Validate the Incrementor type."""
        if isinstance(value, Incrementor) and action != 'update':
            validator.add(name=self.name, message='Incrementors can only be used for updates')
