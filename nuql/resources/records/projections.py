from typing import Any, Dict

from nuql import resources, types
from nuql.fields import Key, String


class Projections:
    def __init__(self, parent: 'resources.Table', serialiser: 'resources.Serialiser') -> None:
        """
        Helper for handling projected fields.

        :arg parent: Parent Table instance.
        :arg serialiser: Serialiser instance.
        """
        self.parent = parent
        self.serialiser = serialiser
        self._store = {}

    def add(self, name: str, value: Any) -> None:
        """
        Adds a projection to the store.

        :arg name: Projected field name.
        :arg value: Value to project.
        """
        field = self.serialiser.get_field(name)

        for key in field.projected_from:
            if key not in self._store:
                self._store[key] = {}
            self._store[key][name] = value

    def merge(self, data: Dict[str, Any], action: 'types.SerialisationType', validator: 'resources.Validator') -> None:
        """
        Merges serialised projections into the record.

        :arg data: Current serialised record.
        :arg action: Serialisation type.
        :arg validator: Validator instance.
        """
        key_fields = {
            key: field
            for key, field in self.parent.fields.items()
            if isinstance(field, Key) or (isinstance(field, String) and field.is_template)
        }

        for key, field in key_fields.items():
            projections = self._store.get(key, {})
            value = field(projections, action, validator)
            if value:
                data[key] = value
