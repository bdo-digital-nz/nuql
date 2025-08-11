__all__ = ['Key']

import re
from typing import Dict, Any

import nuql
from nuql import resources, types
from nuql.resources import EmptyValue


class Key(resources.FieldBase):
    type = 'key'

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
            auto_include_map = {}

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

                auto_include_map[projected_name] = field_map[projected_name].default is not None

            self.auto_include_key_condition = all(auto_include_map.values())

        if self.init_callback is not None:
            self.init_callback(callback)

    def serialise_internal(
            self,
            value: Any,
            action: 'types.SerialisationType',
            validator: 'resources.Validator'
    ) -> Any:
        """
        Internal serialisation override.

        :arg value: Value to serialise.
        :arg action: Serialisation action.
        :arg validator: Validator instance.
        :return: Serialised value.
        """
        serialised = self.serialise_template(value, action, validator)
        if serialised['is_partial']:
            validator.partial_keys.append(self.name)
        return serialised['value']

    def serialise_template(
            self,
            key_dict: Dict[str, Any],
            action: 'types.SerialisationType',
            validator: 'resources.Validator'
    ) -> Dict[str, Any]:
        """
        Serialises the key dict to a string.

        :arg key_dict: Dict to serialise.
        :arg action: Serialisation type.
        :arg validator: Validator instance.
        :return: Serialised representation.
        """
        output = ''
        s = self.sanitise

        if key_dict is None:
            key_dict = {}

        is_partial = False

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

                is_partial = is_partial or (key not in key_dict and not projected_field.default)

                projected_value = key_dict.get(projected_name) or EmptyValue()
                serialised_value = projected_field(projected_value, action, validator)
                used_value = s(serialised_value) if serialised_value else None
            else:
                used_value = s(value)

            # A query might provide only a partial value
            if projected_name is not None and projected_name not in value:
                break

            output += f'{s(key)}:{used_value if used_value else ""}|'

        return {'value': output[:-1], 'is_partial': is_partial}

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
