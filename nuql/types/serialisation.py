__all__ = ['SerialisationType', 'ValidationErrorItem']

from typing import Literal, TypedDict

SerialisationType = Literal['create', 'update', 'write', 'query']


class ValidationErrorItem(TypedDict):
    name: str
    message: str
