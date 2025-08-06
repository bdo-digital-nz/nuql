__all__ = ['validate_condition_dict']

from typing import Dict, Any

import nuql


def validate_condition_dict(condition: Dict[str, Any] | None, required: bool = False) -> None:
    """
    Validates a condition dict when provided.

    :arg condition: Dict or None.
    :param required: If condition is required.
    """
    # Validate empty condition
    if condition is None and not required:
        return None
    elif condition is None and required:
        raise nuql.ValidationError([{'name': 'condition', 'message': 'Condition is required.'}])

    # Type check
    if not isinstance(condition, dict):
        raise nuql.ValidationError([{'name': 'condition', 'message': 'Condition must be a dict.'}])

    # Check where key is present
    if 'where' not in condition or not isinstance(condition['where'], str):
        raise nuql.ValidationError([{
            'name': 'condition.where',
            'message': 'Condition must contain a \'where\' key and must be a string.'
        }])

    # Type check variables
    if 'variables' in condition and not isinstance(condition['variables'], dict):
        raise nuql.ValidationError([{
            'name': 'condition.variables',
            'message': 'Condition variables must be a dict if defined.'
        }])

    # Validate no extra keys were passed
    extra_keys = set(condition.keys()) - {'where', 'variables'}
    if extra_keys:
        raise nuql.ValidationError([{
            'name': 'condition',
            'message': f'Condition contains unexpected keys: {", ".join(extra_keys)}'
        }])
