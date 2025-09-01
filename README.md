# Nuql (pre-release)

Nuql (pronounced "knuckle") is a lightweight AWS DynamoDB library for designing and implementing 
the single table model pattern in Python.

```shell
pip install nuql
```

## Table of Contents
- [Introduction](#introduction)
- [Usage](#usage)
    - [Field Types](#field-types)
    - [Field Options](#field-options)
    - [Generators](#generators)
        - [Datetime Generator](#datetime-generator)
        - [UUID Generator](#uuid-generator)
        - [ULID Generator](#ulid-generator)
    - [Lists](#lists)
    - [Maps](#maps)
    - [Indexes](#indexes)
    - [Keys](#keys)
- [API Reference](#api-reference)
  - [Nuql](#nuql)
    - [Get Table](#get-table)
    - [Batch Writer](#batch-writer)
    - [Transactions](#transactions)
  - [Table](#table)
    - [Query Items](#query-items)
    - [Get Item](#get-item)
    - [Create Item](#create-item)
    - [Update Item](#update-item)
    - [Delete Item](#delete-item)
    - [Put Item](#put-item)
    - [Upsert Item](#upsert-item)
    - [Batch Get](#batch-get)
  - [More Information](#more-information)
    - [Key Condition Expression](#key-condition-expressions)
    - [Filter/Condition Expression](#filtercondition-expressions)

---

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

---

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

### Indexes

Indexes are defined on the `Nuql` class using the `indexes` option. The indexes are defined as 
a list of dicts, where each dict contains the `hash` and `sort` keys. Your indexes are defined 
at the root level, and then each table uses the keys to define the partition and sort keys.

#### Index Config

| Option       | Description                                                                          |
|--------------|--------------------------------------------------------------------------------------|
| `hash`       | The hash key name, required for all indexes.                                         |
| `sort`       | The sort key name for the index.                                                     |
| `type`       | Index type (`local`, `global` or not defined).                                       |
| `name`       | Index name (not required for primary index).                                         |
| `projection` | Projection type (`all` or `keys_only`, `include` is not yet supported).              |
| `follow`     | Retrieve the full item from the primary index if the projection type is `keys_only`. |

---

## API Reference

### Nuql
The `Nuql` class is the main entry point for the library. It is used to instantiate a `Table` 
object for each table in your schema.

---

#### Get Table
`Nuql.get_table(name: str)`

Returns a `Table` object for the given table name.

```python
table = db.get_table('users')
```

---

#### Batch Writer
`Nuql.batch_writer()`

The batch writer is used to put/delete multiple items in a single batch. It is to be used as a
context manager which you make your mutations within:

```python
table = db.get_table('users')

with db.batch_writer() as batch:
    batch.put(table, user)
    batch.delete(table, user)
```

Multiple tables can be written to in the same batch.

---

#### Transactions
`Nuql.transaction()`

A transaction allows you to make multiple mutations to multiple tables in a single atomic 
operation. It is to be used as a context manager which you make your mutations within:

```python
table = db.get_table('users')

with db.transaction() as txn:
    txn.create(table, user)
    txn.delete(table, user)
    txn.update(table, user)
    txn.condition_check(
        table=table, 
        key={'user_id': '123'}, 
        condition={'where': 'is_active eq ${active}', 'variables': {'active': True}}
    )
```

---

### Table

The `Table` class is used to interact with a single table in your schema. It provides all the 
DynamoDB API methods and enables query, put, update and delete items.

---

#### Query Items
`Table.query(...)`

Performs a query on the table.

| Param                 | Description                                                                                                           |
|-----------------------|-----------------------------------------------------------------------------------------------------------------------|
| `key_condition`       | The key condition expression to query (see [Key Condition Expressions](#key-condition-expressions))                   |
| `condition`           | Additional filter expression to apply to the query (see [Filter/Condition Expressions](#filtercondition-expressions)) |
| `limit`               | The maximum number of items to return                                                                                 |
| `exclusive_start_key` | The exclusive start key for the query                                                                                 |
| `consistent_read`     | Whether to use consistent reads                                                                                       |
| `projection`          | The projection expression to apply to the query                                                                       |
| `index`               | The index to query                                                                                                    |

Returns a `dict` with `items` and `last_evaluated_key` keys. If the `last_evaluated_key` is not `None`, 
then you can call the query method again with the `exclusive_start_key` set to the value of the 
`last_evaluated_key` to continue the query.

---

#### Get Item
`Table.get(key: dict, consistent_read: bool = False)`

Retrieves a single item from the table. Will raise `nuql.ItemNotFound` if the item does not exist.

| Param             | Description                                                                                   |
|-------------------|-----------------------------------------------------------------------------------------------|
| `key`             | The key of the item to retrieve (see [Key Condition Expressions](#key-condition-expressions)) |
| `consistent_read` | Whether to use consistent or eventually consistent reads                                      |

Returns a `dict` representing the item.

---

#### Create Item
`Table.create(item: dict, condition: dict | None = None)`

Creates a new item on the table. This method validates that the key is unique.

| Param       | Description                                                                                                                |
|-------------|----------------------------------------------------------------------------------------------------------------------------|
| `item`      | The item to create                                                                                                         |
| `condition` | Additional condition expression to apply to the request (see [Filter/Condition Expressions](#filtercondition-expressions)) |

Returns a `dict` representing the newly created item.

---

#### Update Item
`Table.update(item: dict, condition: dict | None = None)`

Updates an existing item on the table.

| Param       | Description                                                                                                                |
|-------------|----------------------------------------------------------------------------------------------------------------------------|
| `item`      | The item to update                                                                                                         |
| `condition` | Additional condition expression to apply to the request (see [Filter/Condition Expressions](#filtercondition-expressions)) |

Returns a `dict` representing the updated item.

---

#### Delete Item
`Table.delete(key: dict, condition: dict | None = None)`

Deletes an item from the table.

| Param       | Description                                                                                                                |
|-------------|----------------------------------------------------------------------------------------------------------------------------|
| `key`       | The key of the item to delete                                                                                              |
| `condition` | Additional condition expression to apply to the request (see [Filter/Condition Expressions](#filtercondition-expressions)) |

---

#### Put Item
`Table.put(item: dict, condition: dict | None = None)`

Creates or replaces an item on the table.

| Param       | Description                                                                                                                |
|-------------|----------------------------------------------------------------------------------------------------------------------------|
| `item`      | The item to create or replace                                                                                              |
| `condition` | Additional condition expression to apply to the request (see [Filter/Condition Expressions](#filtercondition-expressions)) |

Returns a `dict` representing the item that was put.

---

#### Upsert Item
`Table.upsert(item: dict)`

Creates a new item or updates it if it already exists. If the item does exist then only the provided fields 
will be updated.

| Param  | Description        |
|--------|--------------------|
| `item` | The item to upsert |

Returns a `dict` representing the item that was upserted.

> [!NOTE]
> Condition expressions are not supported for upserts.

---

#### Batch Get
`Table.batch_get(keys: list, consistent_read: bool = False)`

Bulk retrieves items from the table by their keys.

| Param             | Description                                              |
|-------------------|----------------------------------------------------------|
| `keys`            | A list of keys to retrieve                               |
| `consistent_read` | Whether to use consistent or eventually consistent reads |

---

## More Information

### Key Condition Expressions

Key conditions are expressed in a query using a `dict`. The key is always a field name and the value 
is either the value (when using the equals operator) or it is a `dict` with the operator and value:

```python
db_query = table.query(
    key_condition={'tenant_id': '1234', 'user_id': {'begins_with': '0000'}}
)
```

Supported operators are:

| Operator                 | DynamoDB Operator | Notes                                    |
|--------------------------|-------------------|------------------------------------------|
| `equals`                 | `eq`              |                                          |
| `=`                      | `eq`              |                                          |
| `==`                     | `eq`              |                                          |
| `eq`                     | `eq`              |                                          |
| `less_than`              | `lt`              |                                          |
| `<`                      | `lt`              |                                          |
| `lt`                     | `lt`              |                                          |
| `less_than_or_equals`    | `lte`             |                                          |
| `less_than_equals`       | `lte`             |                                          |
| `<=`                     | `lte`             |                                          |
| `greater_than`           | `gt`              |                                          |
| `>`                      | `gt`              |                                          |
| `gt`                     | `gt`              |                                          |
| `greater_than_or_equals` | `gte`             |                                          |
| `greater_than_equals`    | `gte`             |                                          |
| `>=`                     | `gte`             |                                          |
| `begins_with`            | `begins_with`     |                                          |
| `between`                | `between`         | The value must be a `list` of two values |

Projected fields (from [String Templates](#string-templates) or [Keys](#keys)) can be used in the key 
condition expression like normal, and these will project back to the original field they belong to.

You may use one non-equals operator per key or string template field type, and the key condition builder 
will automatically serialise the whole key condition into a single expression:

```python
schema = {
    'users': {
        'pk': {'type': 'key', 'value': {'type': 'user', 'tenant': '${tenant_id}'}},
        'ls1': {'type': 'key', 'value': {'account': '${account_id}', 'created': '${created_at}'}},
        # ... Table fields
        'tenant_id': {'type': 'string', 'required': True},
        'account_id': {'type': 'string', 'required': True},
        'created_at': {'type': 'datetime', 'required': True}
    }
}
```

```python
new_users = table.query({
    'tenant_id': '1234',
    'account_id': '9876',
    'created_at': {'greater_than': datetime.now() + timedelta(days=-7)}
})
```

> [!TIP]
> When passing an incomplete set of projected fields into a query, the query will automatically 
> use the `begins_with` operator for the sort key.

---

### Filter/Condition Expressions