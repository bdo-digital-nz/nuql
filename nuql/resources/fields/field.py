__all__ = ['FieldBase']

from typing import Any, List, Optional

import nuql
from nuql import resources, types


class FieldBase:
    type: str = None

    def __init__(self, name: str, config: 'types.FieldConfig', parent: resources.Table) -> None:
        """
        Wrapper for the handling of field serialisation and deserialisation.

        :arg name: Field name.
        :arg config: Field config dict.
        :arg parent: Parent instance.
        """
        self.name = name
        self.config = config
        self.parent = parent

        # Handle 'KEY' field type
        self.projected_from = []
        self.projects_fields = []

        self.on_init()

    @property
    def hash_key(self) -> bool:
        return self.config.get('hash_key', False)

    @property
    def range_key(self) -> bool:
        return self.config.get('range_key', False)

    @property
    def is_key(self) -> bool:
        return self.hash_key or self.range_key

    @property
    def required(self) -> bool:
        return self.config.get('required', False)

    @property
    def default(self) -> Any:
        return self.config.get('default', None)

    @property
    def value(self) -> Any:
        return self.config.get('value', None)

    @property
    def index_type(self) -> Optional['types.IndexType']:
        return self.config.get('index_type', None)

    @property
    def index_name(self) -> str | None:
        return self.config.get('index_name', None)

    @property
    def on_create(self) -> Optional['types.GeneratorCallback']:
        return self.config.get('on_create', None)

    @property
    def on_update(self) -> Optional['types.GeneratorCallback']:
        return self.config.get('on_update', None)

    @property
    def on_write(self) -> Optional['types.GeneratorCallback']:
        return self.config.get('on_write', None)

    @property
    def validator(self) -> Optional['types.ValidatorCallback']:
        return self.config.get('validator', None)

    @property
    def enum(self) -> List[Any] | None:
        return self.config.get('enum', None)

    def __call__(self, value: Any, action: 'types.SerialisationType', validator: resources.Validator) -> Any:
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
        value = self.serialise(value)

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

    def serialise(self, value: Any) -> Any:
        """
        Serialise/marshal the field value into DynamoDB format.

        :arg value: Deserialised value.
        :return: Serialised value.
        """
        raise nuql.NuqlError(
            code='NotImplementedError',
            message='Serialisation has not been implemented for this field type.'
        )

    def deserialise(self, value: Any) -> Any:
        """
        Deserialise/unmarshal the field value from DynamoDB format.

        :arg value: Serialised value.
        :return: Deserialised value.
        """
        raise nuql.NuqlError(
            code='NotImplementedError',
            message='Deserialisation has not been implemented for this field type.'
        )

    def on_init(self) -> None:
        """Custom initialisation logic for the field."""
