__all__ = ['Map']

from typing import Dict as _Dict, Any

import nuql
from nuql import resources, types


class Map(resources.FieldBase):
    type = 'map'
    fields: _Dict[str, Any] = {}
    serialiser: 'resources.Serialiser' = None

    def on_init(self) -> None:
        """Initialises the dict schema."""
        if 'fields' not in self.config:
            raise nuql.NuqlError(
                code='SchemaError',
                message='Config key \'fields\' must be defined for the dict field type'
            )

        self.fields = resources.create_field_map(self.config['fields'], self.parent, self.parent.provider.fields)
        self.serialiser = resources.Serialiser(self)

    def serialise_internal(
            self,
            value: Any,
            action: 'types.SerialisationType',
            validator: 'resources.Validator'
    ) -> Any:
        """Serialises the Map value"""
        if value:
            return self.serialiser.serialise(action, value, validator)

    def deserialise(self, value: Any) -> Any:
        """Deserialises the Map value"""
        return self.serialiser.deserialise(value)
