from typing import Any, Dict

from nuql.api import Boto3Adapter


class Put(Boto3Adapter):
    def invoke_sync(self, data: Dict[str, Any]) -> Any:
        pass