__all__ = ['FieldConfig', 'IndexType', 'GeneratorCallback', 'ValidatorCallback', 'FieldType']

from typing import TypedDict, NotRequired, Any, Literal, Callable, List, TypeVar, TYPE_CHECKING

from nuql import resources


IndexType = Literal['local', 'global']

GeneratorCallback = Callable[[], Any]
ValidatorCallback = Callable[[Any, resources.Validator], None]

FieldType = TypeVar('FieldType', bound=resources.FieldBase)


class FieldConfig(TypedDict):
    type: str
    hash_key: NotRequired[bool]
    range_key: NotRequired[bool]
    required: NotRequired[bool]
    default: NotRequired[Any]
    value: NotRequired[Any]
    index_type: NotRequired[IndexType]
    index_name: NotRequired[str]
    on_create: NotRequired[GeneratorCallback]
    on_update: NotRequired[GeneratorCallback]
    on_write: NotRequired[GeneratorCallback]
    validator: NotRequired[ValidatorCallback]
    enum: NotRequired[List[Any]]
