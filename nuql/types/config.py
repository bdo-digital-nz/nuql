__all__ = ['TableConfig', 'SchemaConfig', 'DBIndexType', 'IndexesType', 'PrimaryIndex', 'SecondaryIndex']

from typing import Dict, TypedDict, NotRequired, Literal, List

from nuql import types


TableConfig = Dict[str, types.FieldConfig]
SchemaConfig = Dict[str, TableConfig]
DBIndexType = Literal['local', 'global']


class PrimaryIndex(TypedDict):
    hash: str
    sort: NotRequired[str | None]


class SecondaryIndex(TypedDict):
    hash: str
    sort: str
    type: DBIndexType
    name: str


IndexesType = List[PrimaryIndex | SecondaryIndex]
