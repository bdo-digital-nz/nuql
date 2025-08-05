__all__ = ['flatten_dict', 'UpdateKeys', 'UpdateValues', 'Incrementor', 'decrement', 'increment']

from decimal import Decimal
from typing import Dict, Any


def flatten_dict(data: Dict[str, Any], parent: str = None) -> Dict[str, Any]:
    """
    Flattens a nested dict with dot notation keys.

    :arg data: Dict to flatten.
    :param parent: Parent key name if recursive.
    :return: Flattened dict.
    """
    # Default initialiser
    if parent is None:
        parent = ''

    items = []

    for key, value in data.items():
        new_key = (parent + '.' + key) if parent else key

        # Process nested dict
        if isinstance(value, dict):
            if not value:
                items.append((new_key, value))
            else:
                items.extend(flatten_dict(value, new_key).items())

        else:
            items.append((new_key, value))

    return dict(items)


class UpdateKeys:
    def __init__(self) -> None:
        """State manager for keys in an update expression."""
        self.current_index = 0
        self.key_dict = {}

    @property
    def expression_names(self):
        return {value: key for key, value in self.key_dict.items()}

    def add(self, key: str) -> str:
        """
        Parse a key for the update expression.

        :arg key: Key to parse.
        :return: Resulting keys for the update expression.
        """
        keys = []

        # Parse nested parts and see if the key exists in the dictionary
        for part in key.split('.'):
            if part in self.key_dict:
                keys.append(self.key_dict[part])
            else:
                keys.append(f'#key_{self.current_index}')
                self.key_dict[part] = f'#key_{self.current_index}'
                self.current_index += 1

        return '.'.join(keys)


class UpdateValues:
    def __init__(self) -> None:
        """State manager for values in an update expression."""
        self.current_index = 0
        self.values = {}
        self.expressions = []

    def add(self, key: str, value: Any) -> None:
        """
        Add a value to the update expression.

        :arg key: Key in the update expression.
        :arg value: Any value.
        :return: Resulting value key for the update expression.
        """
        value_key = f':val_{self.current_index}'

        if isinstance(value, Incrementor):
            self.values[value_key] = value.value
            self.expressions.append(f'{key} = {key} {"-" if value.negative else "+"} {value_key}')
        else:
            self.values[value_key] = value
            self.expressions.append(f'{key} = {value_key}')

        self.current_index += 1


class Incrementor:
    def __init__(self, value: int | float | Decimal, negative: bool = False) -> None:
        """
        Data class for increment/decrement operations.
        :arg value: Value to increment/decrement.
        :param negative: Set to true to decrement the value.
        """
        if not isinstance(value, Decimal):
            value = Decimal(str(value))

        self.value = value
        self.negative = negative


def increment(value: int | float | Decimal) -> Incrementor:
    """
    Increment a value on an update expression.

    :arg value: Value to increment.
    :return: Incrementor instance.
    """
    return Incrementor(value, negative=False)


def decrement(value: int | float | Decimal) -> Incrementor:
    """
    Decrement a value on an update expression.

    :arg value: Value to decrement.
    :return: Incrementor instance.
    """
    return Incrementor(value, negative=True)
