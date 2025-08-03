__all__ = ['Key']

import re
from typing import Dict, Any

import nuql
from nuql.resources import FieldBase


class Key(FieldBase):
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

    def serialise(self, key_dict: Dict[str, Any]) -> str:
        """
        Serialises the key dict to a string.

        :arg key_dict: Dict to serialise.
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

                projected_value = projected_field.serialise(key_dict.get(key))
                used_value = s(projected_value) if projected_value else None
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

        for item in value.split('|'):
            key, value = item.split(':')
            template_value = self.value.get(key)
            projected_name = self.parse_projected_name(template_value)

            if projected_name in self.projects_fields:
                projected_field = self.parent.fields.get(projected_name)

                if projected_field is None:
                    raise nuql.NuqlError(
                        code='KeySchemaError',
                        message=f'Field \'{projected_name}\' (projected on key '
                                f'\'{self.name}\') is not defined in the schema'
                    )

                output[key] = projected_field.deserialise(value)

            else:
                output[key] = value

        return output

    @staticmethod
    def parse_projected_name(value: str) -> str | None:
        """
        Parses key name in the format '${field_name}'.

        :arg value: Value to parse.
        :return: Field name if it matches the format.
        """
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
