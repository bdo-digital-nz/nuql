__all__ = ['String']

import re
from string import Template
from typing import List, Dict, Any

import nuql
from nuql import resources, types
from nuql.resources import EmptyValue

TEMPLATE_PATTERN = r'\$\{(\w+)}'


class String(resources.FieldBase):
    type = 'string'
    is_template = False

    def on_init(self) -> None:
        """Initialises the string field when a template is defined."""
        self.is_template = self.value is not None and bool(re.search(TEMPLATE_PATTERN, self.value))

        def callback(field_map: dict) -> None:
            """Callback fn to configure projected fields on the schema."""
            auto_include_map = {}

            for key in self.find_projections(self.value):
                if key not in field_map:
                    raise nuql.NuqlError(
                        code='TemplateStringError',
                        message=f'Field \'{key}\' (projected on string field '
                                f'\'{self.name}\') is not defined in the schema'
                    )

                # Add reference to this field on the projected field
                field_map[key].projected_from.append(self.name)
                self.projects_fields.append(key)

                auto_include_map[key] = field_map[key].is_fixed

            self.auto_include_key_condition = all(auto_include_map.values())

        if self.init_callback is not None and self.is_template:
            self.init_callback(callback)

        if self.is_template:
            self.is_fixed = False

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
        if self.is_template:
            serialised = self.serialise_template(value, action, validator)
            if serialised['is_partial']:
                validator.partial_keys.append(self.name)
            return serialised['value']
        else:
            return self.serialise(value)

    def serialise(self, value: str | None) -> str | None:
        """
        Serialises a string value.

        :arg value: Value.
        :return: Serialised value
        """
        return str(value) if value else None

    def deserialise(self, value: str | None) -> str | None:
        """
        Deserialises a string value.

        :arg value: String value.
        :return: String value.
        """
        return str(value) if value else None

    def serialise_template(
            self,
            value: Dict[str, Any],
            action: 'types.SerialisationType',
            validator: 'resources.Validator'
    ) -> Dict[str, Any]:
        """
        Serialises a template string.

        If a required projected value is missing (no user value and no default),
        the output is truncated right before that placeholder and the result is marked partial.

        :arg value: Dict of projections.
        :arg action: Serialisation type.
        :arg validator: Validator instance.
        :return: Dict with 'value' and 'is_partial'.
        """
        if not isinstance(value, dict):
            value = {}

        is_partial = False
        template_str = self.value or ""
        output_parts: list[str] = []

        last_idx = 0

        # Walk through template pieces and placeholders in order
        for match in re.finditer(TEMPLATE_PATTERN, template_str):
            key = match.group(1)
            # Append literal chunk before this placeholder
            literal_chunk = template_str[last_idx:match.start()]

            field = self.parent.fields.get(key)
            if not field:
                raise nuql.NuqlError(
                    code='TemplateStringError',
                    message=f'Field \'{key}\' (projected on string field '
                            f'\'{self.name}\') is not defined in the schema'
                )

            provided = key in value
            provided_value = value.get(key)

            # If not provided and no default, we mark partial and stop right before this placeholder
            if (not provided) and (field.default is None):
                is_partial = True
                # Keep only what we have so far and the literal up to this point
                output_parts.append(literal_chunk)
                break

            # Serialise the projected value (use EmptyValue to allow defaults)
            serialised_value = field(provided_value or EmptyValue(), action, validator)
            serialised_text = serialised_value if serialised_value else ''

            # Append literal + substituted value
            output_parts.append(literal_chunk)
            output_parts.append(str(serialised_text))

            # Advance past this placeholder
            last_idx = match.end()

        # If not partial, append the remaining tail literal
        if not is_partial:
            output_parts.append(template_str[last_idx:])

        return {'value': ''.join(output_parts), 'is_partial': is_partial}

    def deserialise_template(self, value: str | None) -> Dict[str, Any]:
        """
        Deserialises a string template.

        :arg value: String value or None.
        :return: Dict of projections.
        """
        if not value:
            return {}

        pattern = re.sub(TEMPLATE_PATTERN, r'(?P<\1>[^&#]+)', self.value)
        match = re.fullmatch(pattern, value)
        output = {}

        for key, serialised_value in (match.groupdict() if match else {}).items():
            field = self.parent.fields.get(key)

            if not field:
                raise nuql.NuqlError(
                    code='TemplateStringError',
                    message=f'Field \'{key}\' (projected on string field '
                            f'\'{self.name}\') is not defined in the schema'
                )

            deserialised_value = field.deserialise(serialised_value)
            output[key] = deserialised_value

        return output

    @staticmethod
    def find_projections(value: str) -> List[str]:
        """
        Finds projections in the value provided as templates '${field_name}'.

        :arg value: Value to parse.
        :return: List of field names.
        """
        return re.findall(TEMPLATE_PATTERN, value)
