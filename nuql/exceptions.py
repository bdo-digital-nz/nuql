__all__ = ['NuqlError', 'ValidationError', 'Boto3Error', 'ItemNotFound']

from typing import List, Dict, Any

from botocore.exceptions import ClientError

from nuql import types


class NuqlError(Exception):
    def __init__(self, code: str, message: str, **details) -> None:
        """
        Base exception for Nuql.

        :arg code: Error code.
        :arg message: Error message.
        :param details: Arbitrary details to add to the exception.
        """
        self.code = code
        self.message = message
        self.details = details

        super().__init__(f'[{self.code}] {self.message}')


class ValidationError(NuqlError):
    def __init__(self, errors: List['types.ValidationErrorItem']):
        """
        Exception for validation errors during the serialisation process.

        :arg errors: List of ValidationErrorItem dicts.
        """
        self.errors = errors

        formatted_message = 'Schema validation errors occurred:\n\n'

        for error in self.errors:
            formatted_message += f' \'{error["name"]}\': {error["message"]}\n'

        super().__init__('ValidationError', formatted_message)


class Boto3Error(NuqlError):
    def __init__(self, exc: ClientError, request_args: Dict[str, Any]):
        """
        Exception wrapper for boto3 ClientError.

        :arg exc: ClientError instance.
        """
        self.request_args = request_args
        self.error_info = exc.response.get('Error', {})
        self.code = self.error_info.get('Code', 'UnknownError')
        self.message = self.error_info.get('Message', str(exc))

        super().__init__(code=self.code, message=self.message)


class ItemNotFound(NuqlError):
    def __init__(self, key: Dict[str, Any]) -> None:
        """
        Thrown when an item is not found when doing a get_item request.

        :arg key: Key used to retrieve the item.
        """
        self.key = key
        super().__init__('ItemNotFound', f'Item not found: {key}')
