__all__ = ['String']

import re
from string import Template
from typing import List, Dict, Any

import nuql
from nuql import resources, types


TEMPLATE_PATTERN = r'\$\{(\w+)}'


class String(resources.FieldBase):
    type = 'string'
    is_template = False

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
        if not has_value and not value and not self.value and not self.is_template:
            value = self.default

        if self.value and not self.is_template:
            value = self.value

        # Serialise the value
        if self.is_template:
            value = self.serialise_template(value, action, validator)
        else:
            value = self.serialise(value)

        # Validate required field
        if self.required and action == 'create' and value is None:
            validator.add(name=self.name, message='Field is required')

        # Run internal validation
        self.internal_validation(value, action, validator)

        # Run custom validation logic
        if self.validator and action in ['create', 'update', 'write']:
            self.validator(value, validator)

        return value

    def on_init(self) -> None:
        """Initialises the string field when a template is defined."""
        self.is_template = self.value is not None and bool(re.search(TEMPLATE_PATTERN, self.value))

        def callback(field_map: dict) -> None:
            """Callback fn to configure projected fields on the schema."""
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

        if self.init_callback is not None and self.is_template:
            self.init_callback(callback)

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
    ) -> str | None:
        """
        Serialises a template string.

        :arg value: Dict of projections.
        :arg action: Serialisation type.
        :arg validator: Validator instance.
        :return: String value.
        """
        if not isinstance(value, dict):
            value = {}

        # Add not provided keys as empty strings
        for key in self.find_projections(self.value):
            if key not in value:
                value[key] = None

        serialised = {}

        # Serialise values before substituting
        for key, deserialised_value in value.items():
            field = self.parent.fields.get(key)

            if not field:
                raise nuql.NuqlError(
                    code='TemplateStringError',
                    message=f'Field \'{key}\' (projected on string field '
                            f'\'{self.name}\') is not defined in the schema'
                )

            serialised_value = field(deserialised_value, action, validator)
            serialised[key] = serialised_value if serialised_value else ''

        template = Template(self.value)
        return template.substitute(serialised)

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
