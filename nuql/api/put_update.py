__all__ = ['PutUpdate']

from nuql import api


class PutUpdate(api.PutItem):
    serialisation_action = 'create'

    def on_condition(self, condition: 'api.Condition') -> None:
        """
        Sets the condition expression to assert creation.

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
