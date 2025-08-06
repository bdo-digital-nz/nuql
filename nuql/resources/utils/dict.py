__all__ = ['merge_dicts']

from collections.abc import Mapping
from typing import Dict, Any


def merge_dicts(d1: Dict[str, Any], d2: Dict[str, Any] | Mapping):
    """
    Deeply merge two dicts.

    :param d1: First dict.
    :param d2: Second dict.
    :return: Merged dict.
    """
    result = d1.copy()
    for k, v in d2.items():
        if k in result and isinstance(result[k], Mapping) and isinstance(v, Mapping):
            result[k] = merge_dicts(result[k], v)
        else:
            result[k] = v
    return result
