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

        # Serialise the value first
        if not isinstance(value, list):
            value = None
        else:
            value = [self.of(item, action, validator) for item in value]

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

        # Validate required field
        if self.required and action == 'create' and value is None:
            validator.add(name=self.name, message='Field is required')

        # Validate against enum
        if self.enum and has_value and action in ['create', 'update', 'write'] and value not in self.enum:
            validator.add(name=self.name, message=f'Value must be one of: {", ".join(self.enum)}')

        # Run custom validation logic
        if self.validator and action in ['create', 'update', 'write']:
            self.validator(value, validator)

        return value

    def deserialise(self, value: _List[Any] | None) -> _List[Any] | None:
        """
        Deserialises a list of values.

        :arg value: List or None.
        :return: List or None.
        """
        if not isinstance(value, list):
            return None

        return [self.of.deserialise(item) for item in value]
