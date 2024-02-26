# Datasiphon

Package for applying dictionary filter to some form of query on database to retrieve filtered data or acquire filtered query

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install datasiphon.

```bash
pip install datasiphon
```

## Usage

```python
from siphon import sql
import sqlalchemy as sa
# Create a filter
filter_ = {
    "name": {"eq": "John"},
}

table = sa.Table("users", sa.MetaData(), autoload=True, autoload_with=engine)
# Build a query
query = table.select()
# apply filter using build function
query = sql.SQL.build(query, filter_)
# execute query
result = engine.execute(query)
...
```

### Supported Database types
## SQL package (No ORM)
- implemented using `sqlalchemy` package, expected to work with `Table` and `Select` objects
#### Building query
1. Prerequisite
    - base `SELECT` query (`Select` object) from actual `Table` objects (not `text` objects)
    - filter (dictionary), optional, optimally parsed using `qstion` package -> similiar to npm's `qs` package
    - restriction model (child of `siphon.sql.RestrictionModel` class), optional, to restrict the filter to certain fields
2. Usage
```python
from siphon import sql

# Create a filter with strict form
filter_ = {
    "name": {"eq": "John"},
}

# build a query with filter
new_query = sql.SQL.build(query, filter_)
```
- `filter_` is validated before building the query, against columns used in select statement and restriction model (if provided)
 - allowed format represents nestings containing one of :
 1. junctions (AND, OR) -> for combining multiple conditions with desired logical operators (allowed exclusively per nest level)
    ```python
        # Example correct - joining or with different fields
        filter_ = {
            "or":
            {
                "name": {"eq": "John"},
                "age": {"gt": 20}
            }
        }
        
        # example correct - joining or with same field, different operators
        filter_ = {
            "name": {
                "or": {
                    "eq": "John",
                    "ne": "John"
                }
            }
        }
        # Example - incorrect - multiple junctions in same nest level
        filter_ = {
            "or":
            {
                "name": {"eq": "John"},
                "age": {"gt": 20}
            },
            "and":
            {
                "name": {"eq": "John"},
                "age": {"gt": 20}
            }
        }
    ```
 2. operators (eq, ne...) -> for applying conditions on fields -> must always follow a field name (not directly but always has to be nested deeper than field name)
    ```python
    # Example correct - applying eq operator on field name
    filter_ = {
        "name": {"eq": "John"}
        }

    # Example - incorrect - applying eq operator before field name
    filter_ = {
        "eq": {
            "name": "John"
        }
    }
    ```
 3. field name -> for applying conditions on fields -> must always contain an operator (not directly but always has to be nested deeper than field name)
    ```python
    # Example correct - applying eq operator on field name
    filter_ = {
        "name": {"eq": "John"}
        }
    
    # Example - incorrect - applying eq operator before field name
    filter_ = {
        "eq": {
            "name": "John"
        }
    }
    ```
 - if using restriction model, filter also can contain only fields in the restriction model, and operators used have to be in restriction model's field (RestrictionModel class has pretty strict validation for initialization and annotation and won't allow any faulty initialization or usage)
    ```python
    # Example of correct restriction model usage
    class UserRestrictionModel(sql.RestrictionModel):
        # must always be annotated as `list[str]` otherwise will raise an error
        name = list[str] = []
        # must be always subset of all existing operators for that query builder
        age = list[str] = ['eq']
    
    # Example incorrect - using operator not in restriction model
    class UserRestrictionModel(sql.RestrictionModel):
        # does not have correct annotation
        name = list[int] = []
        # does not have correct operators
        age = list[str] = ['eql']
    ```
 - using multiple condition without specifying junctions will result in an `AND` junction between them
    ```python
    # Example correct - applying eq operator on field name
    filter_ = {
        "name": {"eq": "John"},
        "age": {"gt": 20}
        }
    # will be treated as
    filter_ = {
        "and": {
            "name": {"eq": "John"},
            "age": {"gt": 20}
        }
    }

    filter_ = {
        "name": {
            "eq": "John",
            "ne": "John"
            }
    }
    # will be treated as
    filter_ = {
        "and": {
            "name": {
                "eq": "John",
                "ne": "John"
            }
        }
    }
    ```

- generating query: recursively collecting items from filter, and applying filtering directly to exported columns of given query
