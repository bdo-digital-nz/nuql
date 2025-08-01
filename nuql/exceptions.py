__all__ = ['NuqlError', 'ValidationError']

from typing import List

from nuql.types import ValidationErrorItem


class NuqlError(Exception):
    def __init__(self, code: str, message: str, **details) -> None:
        """
        Base exception for Nuql.

        :arg code: Error code.
        :arg message: Error message.
        :param details: Arbitrary details to add to exception.
        """
        self.code = code
        self.message = message
        self.details = details

        super().__init__(f'[{self.code}] {self.message}')


class ValidationError(NuqlError):
    def __init__(self, errors: List[ValidationErrorItem]):
        """
        Exception for validation errors during the serialisation process.

        :arg errors: List of ValidationErrorItem dicts.
        """
        self.errors = errors

        formatted_message = 'Schema validation errors occurred:\n\n'

        for error in self.errors:
            formatted_message += f' \'{error["name"]}\': {error["message"]}\n'

        super().__init__('ValidationError', formatted_message)
