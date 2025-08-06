from typing import Dict as _Dict, Any

from nuql.resources import FieldBase


class Dict(FieldBase):
    type = 'dict'
    fields: _Dict[str, Any] = {}

    def on_init(self) -> None:
        """Initialises the dict schema."""
