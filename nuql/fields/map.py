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

    def __call__(self, value: Any, action: 'types.SerialisationType', validator: 'resources.Validator') -> Any:
        """
        Encapsulates the internal serialisation logic to prepare for
        sending the record to DynamoDB.

        :arg value: Deserialised value.
        :arg action: SerialisationType (`create`, `update`, `write` or `query`).
        :arg validator: Validator instance.
        :return: Serialised value.
        """
        has_value = not isinstance(value, resources.EmptyValue)

        # Apply generators if applicable to the field to overwrite the value
        if action in ['create', 'update', 'write']:
            if action == 'create' and self.on_create:
                value = self.on_create()

            if action == 'update' and self.on_update:
                value = self.on_update()

            if self.on_write:
                value = self.on_write()

        # Set default value if applicable
        if not has_value:
            value = self.default

        # Serialise the value
        if value:
            value = self.serialiser.serialise(action, value, validator)

        # Validate required field
        if self.required and action == 'create' and value is None:
            validator.add(name=self.name, message='Field is required')

        # Run internal validation
        self.internal_validation(value, action, validator)

        # Run custom validation logic
        if self.validator and action in ['create', 'update', 'write']:
            self.validator(value, validator)

        return value
