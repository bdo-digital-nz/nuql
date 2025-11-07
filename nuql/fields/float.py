__all__ = ['Float']

from decimal import Decimal
from typing import Any

from nuql import resources, types
from nuql.api import Incrementor


class Float(resources.FieldBase):
    type = 'float'

    def serialise(self, value: float | Incrementor | None) -> Decimal | Incrementor | None:
        """
        Serialises a float value.

        :arg value: Value as float, Incrementor or None.
        :return: Value as Decimal, Incrementor or None.
        """
        if isinstance(value, Incrementor):
            return value
        try:
            value = float(value)
        except ValueError:
            return None
        return Decimal(str(value))

    def deserialise(self, value: Decimal | None) -> float | None:
        """
        Deserialises a float value.

        :arg value: Value as Decimal or None.
        :return: Value as float or None.
        """
        if not isinstance(value, Decimal):
            return None
        return float(value)

    def internal_validation(self, value: Any, action: 'types.SerialisationType', validator: 'resources.Validator'):
        """Validate the Incrementor type."""
        if isinstance(value, Incrementor) and action != 'update':
            validator.add(name=self.name, message='Incrementors can only be used for updates')
