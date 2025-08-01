from typing import Dict, Any, Optional

import nuql
from nuql import resources, types


class Serialiser:
    def __init__(self, parent: 'resources.Table') -> None:
        """
        Helper object to serialise a record.

        :arg parent: Parent Table or Map.
        """
        self.parent = parent

    def get_field(self, key: str) -> 'resources.FieldBase':
        """
        Get a field instance from the schema.

        :arg key: Field key.
        :return: FieldBase instance.
        """
        if key not in self.parent.fields:
            raise nuql.NuqlError(
                code='FieldNotFound',
                message=f'Field \'{key}\' is not defined in the schema.'
            )
        return self.parent.fields[key]

    def serialise(
            self,
            action: 'types.SerialisationType',
            data: Dict[str, Any] | None = None,
            validator: Optional['resources.Validator'] = None
    ):
        """
        Serialises/marshals a record based on the data provided.

        :arg action: Serialisation type.
        :param data: Data to serialise.
        :param validator: Validator instance.
        :return:
        """
        validator = resources.Validator() if validator is None else validator
        projections = resources.Projections(self.parent, self)
        data = data if data else {}

        # Serialise provided fields
        for key, deserialised_value in data.items():
            field = self.get_field(key)
            serialised_value = field(deserialised_value, action, validator)

            if field.projected_from:
                projections.add(key, serialised_value, action, validator)
            else:
                data[key] = serialised_value

        # Serialise fields not provided (i.e. could have defaults)
        untouched = {name: field for name, field in self.parent.fields.items() if name not in data}
        for name, field in untouched.items():
            if field.projects_fields:
                continue

            serialised_value = field(resources.EmptyValue(), action, validator)

            if field.projected_from:
                projections.add(name, serialised_value, action, validator)
                continue

            if serialised_value:
                data[name] = serialised_value

        # Set projections
        projections.merge(data, action, validator)

        if action in ['create', 'update', 'write']:
            validator.raise_for_validation_errors()

        return data

    def deserialise(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deserialises/unmarshalls data from DynamoDB.

        :arg data: Data to deserialise.
        :return: Deserialised data.
        """
        record = {}

        for name, field in self.parent.fields.items():
            deserialised_value = field.deserialise(data.get(name))

            if field.projected_from:
                continue

            # Directly set field
            record[name] = deserialised_value

            # Handle projected fields
            if field.projects_fields:
                for projected_key in field.projects_fields:
                    projected_field = self.get_field(projected_key)
                    record[projected_key] = projected_field.deserialise(deserialised_value.get(projected_key))

        return record
