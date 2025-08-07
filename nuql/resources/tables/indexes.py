__all__ = ['Indexes']

from typing import Dict, Any, cast

import nuql
from nuql import types


MAX_LSI = 5
MAX_GSI = 20


class Indexes:
    def __init__(self, indexes: 'types.IndexesType') -> None:
        """
        Wrapper class to validate and use indexes for the overall table.

        :arg indexes: List of indexes.
        """
        self.index_keys = set()
        self._indexes = self.validate_indexes(indexes)

    @property
    def primary(self) -> 'types.PrimaryIndex':
        """Retrieve the primary index for the table"""
        return cast(types.PrimaryIndex, self._indexes['primary'])

    def validate_indexes(self, indexes: 'types.IndexesType') -> Dict[str, Dict[str, Any]]:
        """
        Processes, validates and generates index dict for the table.

        :arg indexes: List of indexes.
        :return: Index dict.
        """
        index_dict = {}

        local_count = 0
        global_count = 0

        if not isinstance(indexes, list):
            raise nuql.NuqlError(code='IndexValidation', message='Indexes must be a list')

        for index in indexes:
            if not isinstance(index, dict):
                raise nuql.NuqlError(code='IndexValidation', message='Indexes must be a list of dicts')

            if 'hash' not in index:
                raise nuql.NuqlError(code='IndexValidation', message='\'hash\' is required for all indexes')

            index_name = index.get('name', 'primary')
            self.index_keys.add(index['hash'])

            if 'sort' in index:
                self.index_keys.add(index['sort'])

            # Validate only one primary index
            if index_name == 'primary' and 'primary' in index_dict:
                raise nuql.NuqlError(
                    code='IndexValidation',
                    message='More than one primary index cannot be defined. Did you mean to add \'name\' and \'type\'?'
                )

            # Validate index has a type set
            if index_name != 'primary' and index.get('type') not in ['local', 'global']:
                raise nuql.NuqlError(
                    code='IndexValidation',
                    message='Index type is required for all indexes except the primary index'
                )

            # Set index follow rule
            if index_name != 'primary' and 'follow' in index and not isinstance(index['follow'], bool):
                raise nuql.NuqlError(
                    code='IndexValidation',
                    message='Index \'follow\' must be a boolean value if provided.'
                )

            # Validate index projection
            if index_name != 'primary' and 'projection' in index and index['projection'] not in ['all', 'keys']:
                raise nuql.NuqlError(
                    code='IndexValidation',
                    message='Index \'projection\' must be \'all\' or \'keys\' if provided.'
                )

            # Count LSIs
            if index.get('type') == 'local':
                local_count += 1

            # Count GSIs
            if index.get('type') == 'global':
                global_count += 1

            accepted_keys = ['hash', 'sort', 'name', 'type', 'follow', 'projection']
            extra_keys = [x for x in index.keys() if x not in accepted_keys]
            if extra_keys:
                raise nuql.NuqlError(
                    code='IndexValidation',
                    message=f'Index \'{index_name}\' contains invalid keys: {", ".join(extra_keys)}\n\n'
                            f'Accepted index keys are: {", ".join(accepted_keys)}'
                )

            index_dict[index_name] = index

        # Throw on more than 5 LSIs
        if local_count >= MAX_LSI:
            raise nuql.NuqlError(
                code='IndexValidation',
                message='More than 5 local indexes cannot be defined'
            )

        # Throw on more than 20 GSIs
        if global_count >= MAX_GSI:
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
