# Datasiphon

Package for applying dictionary filter to some form of query on database to retrieve filtered data or acquire filtered query

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install datasiphon.

```bash
pip install datasiphon
```

## Usage

```python
from datasiphon import SqlQueryBuilder
import sqlalchemy as sa
# Create a filter
filter_ = {
    "name": {"eq": "John"},
}

table = sa.Table("users", sa.MetaData(), autoload=True, autoload_with=engine)
# Build a query
query = table.select()

# set up builder with table base
builder = SqlQueryBuilder({"users": table})

# build a query with filter
new_query = builder.build(query, filter_)
```

### Supported Database types
## SQL package (No ORM)
- implemented using `sqlalchemy` package, expected to work with `Table` and `Select` objects
#### Building query
1. Prerequisite
    - base `SELECT` query (`Select` object) from actual `Table` objects (not `text` objects)
    - filter (dictionary/`QsRoot` from `qstion` package), optional, optimally parsed using `qstion` package -> similiar to npm's `qs` package
    - restrictions (optional) - objects that restrict specific columns and operators that can be used in filter
2. Usage
```python
from siphon import sql

# Create a filter with strict form
filter_ = {
    "name": {"eq": "John"},
}

# build a query with filter
new_query = sql.SqlQueryBuilder({"users": table}).build(query, filter_)
```
- `filter_` is validated before building the query, expecting specific format representing valid structure of applicable filter for given backend (currently only SQL backend is supported)
 - allowed format represents nestings containing one of :
 1. junctions (AND, OR) -> for combining multiple conditions with desired logical operators
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
 - if using restriction model - builder will raise error when trying to apply operator that is restricted for given field (column)
    ```python
    from siphon import ColumnFilterRestriction, AnyValue
    from siphon.sql_filter import SQLEq, SQLNe
    # Example of correct restriction model usage
    # This restriction will forbid applying eq operator on field `name` - AnyValue signifies that any value is forbidden
    restriction = ColumnFilterRestriction(
        "name", SQLEq.generate_restriction(AnyValue)
    )
    # Example of specific value restriction
    # This restriction will forbid applying eq operator on field `name` with value "John"
    restriction = ColumnFilterRestriction(
        "name", SQLEq.generate_restriction("John")
    )
    # Alternate approach to generate restriction
    restriction = ColumnFilterRestriction.from_dict(
        "name", {"eq": AnyValue}
    )
    restriction = ColumnFilterRestriction.from_dict(
        "name", {"eq": "John"}
    )

    # Applying restriction to builder
    builder = SqlQueryBuilder({"users": table})
    # Restrictions are optional positional argument
    builder.build(query, filter_, restriction)
    
    # different restriction for different column
    age_restriction = ColumnFilterRestriction(
        "age", SQLNe.generate_restriction(20)
    )
    builder.build(query, filter_, restriction, age_restriction)
        
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
#### Manipulating `FilterExpression` object
- `FilterExpression` object is a tree-like structure representing filter dictionary in a way that can be easily manipulated
- Expressions can be added via `add_expression` method
- Expressions can be replaced via `replace_expression` method
- Expressions can be removed via `remove_expression` method
- Expressions can be retrieved via `find_expression` method

#### Reconstructing filter from `FilterExpression` and `SqlKeywordFilter` objects

- since `FilterExpression` object is a tree-like structure builded originally from filter dictionary, it can be easily reconstructed along with `SqlKeywordFilter` object to represent the same filter as original dictionary
- this objects can be manipulated directly to adjust filter or to be used in different context
