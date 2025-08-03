__all__ = ['Indexes']

from typing import Dict, Any, cast

import nuql
from nuql import types


class Indexes:
    def __init__(self, indexes: 'types.IndexesType') -> None:
        """
        Wrapper class to validate and use indexes for the overall table.

        :arg indexes: List of indexes.
        """
        self._indexes = self.validate_indexes(indexes)

    @property
    def primary(self) -> 'types.PrimaryIndex':
        """Retrieve the primary index for the table"""
        return cast(types.PrimaryIndex, self._indexes['primary'])

    @staticmethod
    def validate_indexes(indexes: 'types.IndexesType') -> Dict[str, Dict[str, Any]]:
        """
        Processes, validates and generates index dict for the table.

        :arg indexes: List of indexes.
        :return: Index dict.
        """
        index_dict = {}

        local_count = 0
        global_count = 0

        for index in indexes:
            index_name = index.get('name', 'primary')

            # Validate only one primary index
            if index_name == 'primary' and 'primary' in index_dict:
                raise nuql.NuqlError(
                    code='MultiplePrimaryIndexes',
                    message='More than one primary index cannot be defined'
                )

            # Validate index has a type set
            if index_name != 'primary' and index.get('type') not in ['local', 'global']:
                raise nuql.NuqlError(
                    code='MissingIndexType',
                    message='Index type is required for all indexes except the primary index'
                )

            # Count LSIs
            if index.get('type') == 'local':
                local_count += 1

            # Count GSIs
            if index.get('type') == 'global':
                global_count += 1

            index_dict[index_name] = index

        # Throw on more than 5 LSIs
        if local_count >= 5:
            raise nuql.NuqlError(
                code='IndexValidation',
                message='More than 5 local indexes cannot be defined'
            )

        # Throw on more than 20 GSIs
        if global_count >= 20:
            raise nuql.NuqlError(
                code='IndexValidation',
                message='More than 20 global indexes cannot be defined'
            )

        return index_dict

    def get_index(self, name: str) -> 'types.SecondaryIndex':
        """
        Get a secondary index by name.

        :arg name: Index name.
        :return: SecondaryIndex dict.
        """
        # Throw on accessing primary to keep logical separation
        if name == 'primary':
            raise nuql.NuqlError(
                code='InvalidIndex',
                message='The primary index cannot be accessed using get_index, please use the primary attribute instead'
            )

        # Validate index exists
        if name not in self._indexes:
            raise nuql.NuqlError(
                code='InvalidIndex',
                message=f'Index \'{name}\' is not defined for this DynamoDB table'
            )

        return cast(types.SecondaryIndex, self._indexes[name])
