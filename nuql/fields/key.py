__all__ = ['Key']

import re
from typing import Dict, Any

import nuql
from nuql import resources, types


class Key(resources.FieldBase):
    type = 'key'

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
        if not has_value and not value:
            value = self.default

        # Serialise the value
        value = self.serialise_template(value, action, validator)

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

    def on_init(self) -> None:
        """Initialises the key field."""
        # Validate the field has a value
        if self.value is None:
            raise nuql.NuqlError(
                code='KeySchemaError',
                message='\'value\' must be defined for a key field'
            )

        # Callback fn handles configuring projected fields on the schema
        def callback(field_map: dict) -> None:
            """Callback fn to configure projected fields on the schema."""
            for key, value in self.value.items():
                projected_name = self.parse_projected_name(value)

                # Skip fixed value fields
                if not projected_name:
                    continue

                # Validate projected key exists on the table
                if projected_name not in field_map:
                    raise nuql.NuqlError(
                        code='KeySchemaError',
                        message=f'Field \'{projected_name}\' (projected on key '
                                f'\'{self.name}\') is not defined in the schema'
                    )

                # Add reference to this field on the projected field
                field_map[projected_name].projected_from.append(self.name)
                self.projects_fields.append(projected_name)

        if self.init_callback is not None:
            self.init_callback(callback)

    def serialise_template(
            self,
            key_dict: Dict[str, Any],
            action: 'types.SerialisationType',
            validator: 'resources.Validator'
    ) -> str:
        """
        Serialises the key dict to a string.

        :arg key_dict: Dict to serialise.
        :arg action: Serialisation type.
        :arg validator: Validator instance.
        :return: Serialised representation.
        """
        output = ''
        s = self.sanitise

        for key, value in self.value.items():
            projected_name = self.parse_projected_name(value)

            if projected_name in self.projects_fields:
                projected_field = self.parent.fields.get(projected_name)

                if projected_field is None:
                    raise nuql.NuqlError(
                        code='KeySchemaError',
                        message=f'Field \'{projected_name}\' (projected on key '
                                f'\'{self.name}\') is not defined in the schema'
                    )

                projected_value = key_dict.get(projected_name)
                serialised_value = projected_field(projected_value, action, validator)
                used_value = s(serialised_value) if serialised_value else None
            else:
                used_value = s(value)

            # A query might provide only a partial value
            if projected_name is not None and projected_name not in value:
                break

            output += f'{s(key)}:{used_value if used_value else ""}|'

        return output[:-1]

    def deserialise(self, value: str) -> Dict[str, Any]:
        """
        Deserialises the key string to a dict.

        :arg value: String key value.
        :return: Key dict.
        """
        output = {}

        if value is None:
            return output

        unmarshalled = {
            key: serialised_value
            if serialised_value else None
            for key, serialised_value in [item.split(':') for item in value.split('|')]
        }

        for key, serialised_value in self.value.items():
            provided_value = unmarshalled.get(key)
            projected_name = self.parse_projected_name(serialised_value)

            if projected_name in self.projects_fields:
                projected_field = self.parent.fields.get(projected_name)

                if projected_field is None:
                    raise nuql.NuqlError(
                        code='KeySchemaError',
                        message=f'Field \'{projected_name}\' (projected on key '
                                f'\'{self.name}\') is not defined in the schema'
                    )

                deserialised_value = projected_field.deserialise(provided_value)
                output[projected_name] = deserialised_value
            else:
                output[key] = provided_value

        return output

    @staticmethod
    def parse_projected_name(value: str) -> str | None:
        """
        Parses key name in the format '${field_name}'.

        :arg value: Value to parse.
        :return: Field name if it matches the format.
        """
        if not isinstance(value, str):
            return None
        match = re.search(r'\$\{([a-zA-Z0-9_]+)}', value)
        if not match:
            return None
        else:
            return match.group(1)

    @staticmethod
    def sanitise(value: str) -> str:
        """
        Sanitises the input to avoid conflict with serialisation/deserialisation.

        :arg value: String value.
        :return: Sanitised string value.
        """
        if not isinstance(value, str):
            value = str(value)

        for character in [':', '|']:
            value = value.replace(character, '')

        return value
