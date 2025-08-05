__all__ = ['UpdateItem']

from typing import Any, Dict, Optional, Literal

from botocore.exceptions import ClientError

import nuql
from nuql import types, api


class UpdateItem(api.Boto3Adapter):
    serialisation_action: Literal['create', 'update'] = 'update'

    def on_condition(self, condition: 'api.Condition') -> None:
        """
        Make changes to the condition expression before request.

        :arg condition: Condition instance.
        """
        index = self.table.indexes.primary
        keys = [index['hash']]

        # Append sort key if defined in primary index, but only if it exists in the schema
        if 'sort' in index and index['sort'] and index['sort'] in self.table.fields:
            keys.append(index['sort'])

        expression = ' and '.join([f'attribute_exists({key})' for key in keys])

        # Add the expression to the existing condition
        condition.append(expression)

    def invoke_sync(
            self,
            data: Dict[str, Any],
            condition: Optional['types.QueryWhere'] = None,
            shallow: bool = False
    ) -> Dict[str, Any]:
        """
        Updates an item in the table.

        :arg data: Data to update.
        :param condition: Optional condition expression.
        :param shallow: Activates shallow update mode (so that whole nested items are updated at once).
        :return: New item dict.
        """
        # Serialise the data for update
        key = self.table.serialiser.serialise_key(data)
        serialised_data = {k: v for k, v in self.table.serialiser.serialise('update', data).items() if k not in key}

        # Generate the update condition
        condition = api.Condition(
            table=self.table,
            condition=condition,
            condition_type='ConditionExpression'
        )

        # Generate the update expression
        update = api.UpdateExpressionBuilder(serialised_data, shallow=shallow)
        args = {'Key': key, **update.args, **condition.args, 'ReturnValues': 'ALL_NEW'}

        try:
            response = self.connection.table.update_item(**args)
        except ClientError as exc:
            raise nuql.Boto3Error(exc, args)

        return self.table.serialiser.deserialise(response['Attributes'])
