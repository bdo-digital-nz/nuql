__all__ = ['validate_condition_dict', 'validate_schema']

import inspect
from typing import Dict, Any, List, Type

import nuql
from nuql import types, resources


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


def validate_table(name: str, config: Dict[str, Any], fields: Dict[str, Type['types.FieldType']]) -> None:
    """
    Validate a table.

    :arg name: Table name.
    :arg config: Table config.
    :arg fields: Field map.
    """
    if not isinstance(config, dict):
        raise nuql.ValidationError([{
            'name': f'schema.tables.{name}',
            'message': 'Table config must be a dict.'
        }])

    for field_name, field_config in config.items():
        if not isinstance(field_name, str):
            raise nuql.ValidationError([{
                'name': f'schema.tables.{name}.fields',
                'message': 'All field names in table config must be a string.'
            }])

        if not isinstance(field_config, dict):
            raise nuql.ValidationError([{
                'name': f'schema.tables.{name}.fields.{field_name}',
                'message': 'Field config must be a dict.'
            }])

        field_type = field_config.get('type')

        if not field_type:
            raise nuql.ValidationError([{
                'name': f'schema.tables.{name}.fields.{field_name}.type',
                'message': 'Field type is required.'
            }])

        if field_type not in fields:
            raise nuql.ValidationError([{
                'name': f'schema.tables.{name}.fields.{field_name}.type',
                'message': f'Field type \'{field_type}\' is not defined.'
            }])

        if 'required' in field_config and not isinstance(field_config['required'], bool):
            raise nuql.ValidationError([{
                'name': f'schema.tables.{name}.fields.{field_name}.required',
                'message': 'Field key \'required\' must be a boolean value if provided.'
            }])

        if 'on_create' in field_config and not inspect.isfunction(field_config['on_create']):
            raise nuql.ValidationError([{
                'name': f'schema.tables.{name}.fields.{field_name}.on_create',
                'message': 'Field key \'on_create\' must be a function if provided.'
            }])

        if 'on_update' in field_config and not inspect.isfunction(field_config['on_update']):
            raise nuql.ValidationError([{
                'name': f'schema.tables.{name}.fields.{field_name}.on_update',
                'message': 'Field key \'on_update\' must be a function if provided.'
            }])

        if 'on_write' in field_config and not inspect.isfunction(field_config['on_write']):
            raise nuql.ValidationError([{
                'name': f'schema.tables.{name}.fields.{field_name}.on_write',
                'message': 'Field key \'on_write\' must be a function if provided.'
            }])

        if 'validator' in field_config and not inspect.isfunction(field_config['validator']):
            raise nuql.ValidationError([{
                'name': f'schema.tables.{name}.fields.{field_name}.validator',
                'message': 'Field key \'validator\' must be a function if provided.'
            }])

        if 'enum' in field_config and not isinstance(field_config['enum'], list):
            raise nuql.ValidationError([{
                'name': f'schema.tables.{name}.fields.{field_name}.enum',
                'message': 'Field key \'enum\' must be a list if provided.'
            }])

        accepted_keys = [
            'type', 'required', 'default', 'value', 'on_create', 'on_update', 'on_write', 'validator', 'enum',
            'of', 'fields',
        ]
        invalid_field_config_keys = [x for x in field_config.keys() if x not in accepted_keys]
        if invalid_field_config_keys:
            raise nuql.ValidationError([{
                'name': f'schema.tables.{name}.fields.{field_name}',
                'message': f'Field config contains unexpected keys: {", ".join(invalid_field_config_keys)}. '
                           f'Accepted keys are: {", ".join(accepted_keys)}'
            }])


def validate_schema(schema: Dict[str, Any], fields: List[Type['types.FieldType']]) -> None:
    """
    Validate a schema.

    :arg schema: Schema dict.
    :arg fields: List of fields passed from client.
    """
    fields = resources.get_field_types(fields)

    # Type check schema
    if not isinstance(schema, dict):
        raise nuql.ValidationError([{
            'name': 'schema',
            'message': 'Schema must be a dict.'
        }])

    for table_name, config in schema.items():
        # Type check table name
        if not isinstance(table_name, str):
            raise nuql.ValidationError([{
                'name': 'schema.table_name',
                'message': 'Table name in schema must be a string.',
            }])

        # Validate table schema
        validate_table(table_name, config, fields)
