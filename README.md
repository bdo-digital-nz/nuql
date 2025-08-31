# Nuql (pre-release)

Nuql (pronounced "knuckle") is a lightweight AWS DynamoDB library for designing and implementing 
the single table model pattern in Python.

```shell
pip install nuql
```

## Introduction

The design of your single table model schema is passed as a `dict` into the `Nuql` class and allows 
you to instantiate a `Table`. The `Table` class provides all the DynamoDB API methods and enables 
querying, putting, updating and deleting items. The library automatically handles serialisation and 
deserialisation of your data based on the schema design for each table.

```python
from nuql import Nuql

schema = {
    'users': {
        'pk': {'type': 'string'},
        'name': {'type': 'string', 'required': True},
        'active': {'type': 'boolean', 'default': True},
    },
    'widgets': {
        'pk': {'type': 'string'},
        'size': {'type': 'integer'},
        'price': {'type': 'float', 'required': True},
    }
}

indexes = [{'hash': 'pk'}]

db = Nuql('my-table-name', schema=schema, indexes=indexes)
```

In the above example we have defined two tables, `users` and `widgets`. The `pk` field is defined 
as the partition/hash key in the indexes, and then both tables define `pk` as a string. These 
tables can then be used to query, put, update and delete items.

```python
users_table = db.get_table('users')

# Create a new user
user = users_table.create({'pk': 'USER#123', 'name': 'John Smith'})

# Update the user
user['active'] = False
users_table.update(user)
```

## Usage

### Field Types

The library supports the following field types out of the box:

| Type                 | Description                                                                                 |
|----------------------|---------------------------------------------------------------------------------------------|
| `string`             | A string value                                                                              |
| `integer`            | An integer value                                                                            |
| `float`              | A floating point value                                                                      |
| `boolean`            | A boolean value                                                                             |
| `datetime`           | A timezone-aware datetime value                                                             |
| `datetime_timestamp` | A timezone-aware datetime value that serialises to a timestamp `int` (can be used as a TTL) |
| `list`               | A list of values                                                                            |
| `map`                | A map of key-value pairs                                                                    |
| `uuid`               | A UUID value                                                                                |
| `ulid`               | A ULID value (depends on the `python-ulid` package)                                         |
| `key`                | A key value string that serialises from a dict (to create a composite key)                  |

You can also define your own field types by subclassing the `Field` class:

```python
from nuql.resources import FieldBase


class GarbledString(FieldBase):
    type = 'garbled_string'

    def serialise(self, value: str) -> str:
        return 'garbled' + value + 'garbled'
    
    def deserialise(self, value: str) -> str:
        return value[8:-8]

```

These custom field types can then be added to the `custom_fields` list on the `Nuql` class:

```python
db = Nuql(..., custom_fields=[GarbledString])
```

### Field Options

There are several configuration options that can be applied to the field dict within your table schema. 
These options control how the field is serialised and can set several rules:

| Option      | Description                                                                               |
|-------------|-------------------------------------------------------------------------------------------|
| `type`      | The field type (required)                                                                 |
| `required`  | Whether the field is required (enforced only when specifically creating a record)         |
| `default`   | The default value for the field                                                           |
| `value`     | Used as a fixed field value, or to configure a `key` field                                |
| `on_update` | A function that is called to get a value when a record is updated                         |
| `on_create` | A function that is called to get a value when a record is created                         |
| `on_write`  | A function that is called to get a value when a record is written (create, update or put) |
| `validator` | A custom field validator function                                                         |
| `enum`      | A list of accepted values for the field                                                   |

### Generators

A generator is a function called to generate a value for a field when a record is created, 
updated or written. This generator function takes no arguments and returns a value that is 
then serialised before being written to DynamoDB.

#### Datetime Generator

The library includes a generator for generating timezone-aware datetime values:

```python
from nuql.generators import Datetime

schema = {
    'users': {
        # Table fields...
        'created_at': {'type': 'datetime', 'on_create': Datetime.now()},
        'expires_at': {'type': 'datetime', 'on_create': Datetime.relative(days=30)}
    }
}
```

#### UUID Generator

The library also includes a generator for generating UUID values. These can either be a 
v4 UUID or a v7 UUID (depends on the `uuid-utils` package):

```python
from nuql.generators import Uuid

schema = {
    'users': {
        # Table fields...
        'v4': {'type': 'uuid', 'on_create': Uuid.v4()},
        'v7': {'type': 'uuid', 'on_create': Uuid.v7()}
    }
}
```

#### ULID Generator

Finally, the library includes a generator for generating ULID values:

```python
from nuql.generators import Ulid

schema = {
    'users': {
        # Table fields...
        'ulid': {'type': 'ulid', 'on_create': Ulid.now()}
    }
}
```

### Lists

A list field type can be defined, and the definition of that list is configured using the `of` config option:

```python
schema = {
    'users': {
        # Table fields
        'tags': {'type': 'list', 'of': {'type': 'string', 'enum': ['cool', 'very cool', 'awesome']}}
    }
}
```

### Maps

The map field type almost operates as an independent schema with its own fields and serialisation.

```python
schema = {
    'users': {
        # Table fields
        'settings': {
            'type': 'map',
            'fields': {
                'wearing_a_hat': {'type': 'boolean'},
                'wearing_socks': {'type': 'boolean'},
            }
        },
        'friends': {
            'type': 'list',
            'of': {
                'type': 'map',
                'fields': {
                    'name': {'type': 'string'},
                    'age': {'type': 'integer'},
                }
            }
        }
    }
}
```

### String Templates

In the spirit of the single table model pattern, the library allows you to define string templates 
which can bring multiple fields together to create a composite key. The design of the template is 
provided to the `value` option of a string field and references other fields at the root level of 
the schema by wrapping the field name in a template `${my_field}`:

```python
schema = {
    'users': {
        'pk': {'type': 'string', 'value': 'TENANT#${tenant_id}'},
        'sk': {'type': 'string', 'value': 'USER#${user_id}'},
        'tenant_id': {'type': 'string', 'required': True},
        'user_id': {'type': 'string', 'required': True}
    }
}
```

This gives a more ergonomic way of defining and using composite keys, especially when querying 
the table. Instead of manually constructing these composite keys for a query, you can just 
use the `tenant_id` and `user_id` fields in the query, and it will automatically project 
these values on to the `pk` and `sk` fields.

### Keys

Much like with the concept of string templates, the `key` field type can achieve a similar 
effect by designing the key with a dict. Like with the string templates this is also specified 
using the `value` option. The value of this dict will accept either a fixed string value or a 
field variable `${my_field}`:

```python
schema = {
    'users': {
        'pk': {'type': 'key', 'value': {'type': 'user', 'tenant_id': '${tenant_id}'}},
        'tenant_id': {'type': 'string', 'required': True}
    }
}
```

In practice both the string templates and keys operate in the same manner when querying.

> [!TIP] A query with a key condition that generates a partial composite key will automatically 
> use the `begins_with` operator, but only for the sort key. The hash key always requires a 
> complete key.
