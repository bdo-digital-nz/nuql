__all__ = ['QueryWhere', 'QueryResult']

from typing import TypedDict, NotRequired, Dict, Any, List


class QueryWhere(TypedDict):
    where: str
    variables: NotRequired[Dict[str, Any]]


class QueryResult(TypedDict):
    items: List[Dict[str, Any]]
    last_evaluated_key: Dict[str, Any] | None
