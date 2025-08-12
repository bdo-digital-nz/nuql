__all__ = ['List']

from typing import List as _List, Any

import nuql
from nuql import resources, types
from nuql.resources import FieldBase


class List(FieldBase):
    type = 'list'
    of: FieldBase

    def on_init(self) -> None:
        """Defines the contents of the list."""
        if 'of' not in self.config:
            raise nuql.NuqlError(
                code='SchemaError',
                message='Config key \'of\' must be defined for the list field type'
            )

        # Initialise the configured 'of' field type
        field_map = resources.create_field_map(
            fields={'of': self.config['of']},
            parent=self.parent,
            field_types=self.parent.provider.fields
        )
        self.of = field_map['of']

    def serialise_internal(
            self,
            value: Any,
            action: 'types.SerialisationType',
            validator: 'resources.Validator'
    ) -> Any:
        """Internal serialisation"""
        if not isinstance(value, list):
            return None
        else:
            return [self.of(item, action, validator) for item in value]

    def deserialise(self, value: _List[Any] | None) -> _List[Any] | None:
        """
        Deserialises a list of values.

        :arg value: List or None.
        :return: List or None.
        """
        if not isinstance(value, list):
            return None

        return [self.of.deserialise(item) for item in value]
