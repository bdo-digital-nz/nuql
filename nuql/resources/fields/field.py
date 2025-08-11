__all__ = ['FieldBase']

from typing import Any, List, Optional, Callable

import nuql
from nuql import resources, types


class FieldBase:
    type: str = None

    def __init__(
            self,
            name: str,
            config: 'types.FieldConfig',
            parent: 'resources.Table',
            init_callback: Callable[[Callable], None] | None = None
    ) -> None:
        """
        Wrapper for the handling of field serialisation and deserialisation.

        :arg name: Field name.
        :arg config: Field config dict.
        :arg parent: Parent instance.
        :param init_callback: Optional init callback.
        """
        self.name = name
        self.config = config
        self.parent = parent
        self.init_callback = init_callback
        self.auto_include_key_condition = False

        # Handle 'KEY' field type
        self.projected_from = []
        self.projects_fields = []

        self.on_init()

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
        if not has_value and self.default:
            value = self.default

        # Serialise the value
        value = self.serialise_internal(value, action, validator)

        # Validate required field
        if self.required and action == 'create' and value is None:
            validator.add(name=self.name, message='Field is required')

        # Validate against enum
        if self.enum and has_value and action in ['create', 'update', 'write'] and value not in self.enum:
            validator.add(name=self.name, message=f'Value must be one of: {", ".join(self.enum)}')

        # Run internal validation
        self.internal_validation(value, action, validator)

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

    def serialise_internal(
            self,
            value: Any,
            _action: 'types.SerialisationType',
            _validator: 'resources.Validator'
    ) -> Any:
        """
        Internal serialisation wrapper to allow overridable serialisation behaviour.

        :arg value: Value to serialise.
        :arg _action: Serialisation type.
        :arg _validator: Validator instance.
        :return: Serialised value.
        """
        return self.serialise(value)

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
        pass

    def internal_validation(self, value: Any, action: 'types.SerialisationType', validator: 'resources.Validator'):
        """
        Perform internal validation on the field.

        :arg value: Value.
        :arg action: Serialisation action.
        :arg validator: Validator instance.
        """
        pass
