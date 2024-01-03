# Datasiphon

Package for applying dictionary filter to some form of query on database to retrieve filtered data or acquire filtered query

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install datasiphon.

```bash
pip install datasiphon
```

## Usage

```python
from siphon import build, sql
import sqlalchemy as sa
# Create a filter
filter_ = {
    "name": {"eq": "John"},
}

table = sa.Table("users", sa.MetaData(), autoload=True, autoload_with=engine)
# Build a query
query = table.select()
# apply filter using build function
query = build(query, sql.SQl, filter_)
# execute query
result = engine.execute(query)
...
```

## Currently Supported Databases

- SQL (using sqlalchemy)
