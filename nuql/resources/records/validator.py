__all__ = ['Validator']

import nuql


class Validator:
    def __init__(self, parent: 'Validator' = None, path: str | None = None) -> None:
        """
        Validation helper class to pick up serialisation errors.

        :param parent: Parent Validator instance if applicable.
        :param path: Path (where nested).
        """
        self.parent = parent
        self.path = path
        self.children = []
        self._errors = []

    @property
    def errors(self):
        """Recursively provide errors."""
        return [*self._errors, *[x.errors for x in self.children]]

    def spawn_new(self, path: str) -> 'Validator':
        """
        Spawns a new validator instance for nested validation.

        :arg path: Path of new validator.
        :return: Validator instance.
        """
        full_path = self.path + '.' + path if self.path else path
        validator = Validator(parent=self, path=full_path)
        self.children.append(validator)
        return validator

    def add(self, name: str, message: str) -> None:
        """
        Adds a validation error.

        :arg name: Field name.
        :arg message: Error message.
        """
        self._errors.append({'name': self.path + '.' + name if self.path else name, 'message': message})

    def raise_for_validation_errors(self):
        """Raises a ValidationError exception if there are any errors."""
        if self._errors:
            raise nuql.ValidationError(self.errors)
