from typing import Dict, Any, Optional, Union

import nuql
from nuql import resources, types, fields


class Serialiser:
    def __init__(self, parent: Union['resources.Table', 'fields.Map']) -> None:
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
        output = {}

        # Serialise provided fields
        for key, deserialised_value in data.items():
            field = self.get_field(key)

            if not field:
                raise nuql.NuqlError(
                    code='SchemaError',
                    message=f'Field \'{key}\' is not defined in the schema.'
                )

            # Skip serialisation for projected fields as this is to be handled at
            # the end of the serialisation process
            if field.projected_from:
                projections.add(key, deserialised_value)
            else:
                serialised_value = field(deserialised_value, action, validator)
                output[key] = serialised_value

        # Serialise fields not provided (i.e. could have defaults)
        untouched = {name: field for name, field in self.parent.fields.items() if name not in data}
        for name, field in untouched.items():
            if field.projects_fields:
                continue

            if field.projected_from:
                continue

            serialised_value = field(resources.EmptyValue(), action, validator)
            output[name] = serialised_value

        # Set projections
        projections.merge(output, action, validator)

        if action in ['create', 'update', 'write']:
            validator.raise_for_validation_errors()

        return output

    def serialise_key(self, key: Dict[str, Any], index_name: str = 'primary') -> Dict[str, Any]:
        """
        Serialises the key for an item on a given index.

        :arg key: Key to serialise.
        :param index_name: Index name to serialise key for.
        :return: Serialised key.
        """
        # Check parent is of a valid type
        if not isinstance(self.parent, resources.Table):
            raise nuql.NuqlError(
                code='InvalidTable',
                message='Serialisation of keys is only supported for Table resources.'
            )

        # Get applicable index
        if index_name == 'primary':
            index = self.parent.indexes.primary
        else:
            index = self.parent.indexes.get_index(index_name)

        # Serialise provided data according the the schema
        serialised_key = self.serialise('query', key)

        # Produce a key from the serialised result and for the given index
        return {
            key: value
            for key, value in serialised_key.items()
            if key == index['hash'] or ('sort' not in index or key == index['sort'])
        }

    def deserialise(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deserialises/unmarshalls data from DynamoDB.

        :arg data: Data to deserialise.
        :return: Deserialised data.
        """
        record = {}

        for name, field in self.parent.fields.items():
            # Special Case: string templates
            if hasattr(field, 'deserialise_template') and getattr(field, 'is_template', True):
                deserialised_value = field.deserialise_template(data.get(name))
            else:
                deserialised_value = field.deserialise(data.get(name))

            if field.projected_from:
                continue

            # Directly set field
            record[name] = deserialised_value

            # Handle projected fields
            if field.projects_fields:
                for projected_key in field.projects_fields:
                    record[projected_key] = deserialised_value.get(projected_key)

        return record
