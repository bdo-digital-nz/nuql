from typing import Any, Dict

from nuql import resources, types


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

    def add(self, name: str, value: Any, action: 'types.SerialisationType', validator: 'resources.Validator') -> None:
        """
        Adds a projection to the store.

        :arg name: Projected field name.
        :arg value: Value to project.
        :arg action: Serialisation type.
        :arg validator: Validator instance.
        """
        field = self.serialiser.get_field(name)

        for key in field.projected_from:
            if key not in self._store:
                self._store[key] = {}
            self._store[key][name] = field(value, action, validator)

    def merge(self, data: Dict[str, Any], action: 'types.SerialisationType', validator: 'resources.Validator') -> None:
        """
        Merges serialised projections into the record.

        :arg data: Current serialised record.
        :arg action: Serialisation type.
        :arg validator: Validator instance.
        """
        for name, projections in self._store.items():
            field = self.serialiser.get_field(name)

            has_values = any([x is not None for x in projections.values()])

            if has_values:
                data[name] = field(projections, action, validator)
