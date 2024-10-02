# Changelog

All notable changes to [qstion](https://github.com/kajotgames/qstion) project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).
### [0.3.7] - 2024-10-02

- added support for advanced ordering null values in `SQL` backend using nulls last and nulls first methods
- adjusted operators `eq` and `ne` - correct handling of bool type columns and `None` values

### [0.3.5] - 2024-09-23

- adjusted dumping expression to avoid merging junctions which would result in incorrect query - now dumped into array like dict


### [0.3.0] - 2024-09-10

- Refactored project - core structure moved to `core` module, sql backend moved to is now in `sql_filter` module
- Rewritten tests
- Modified structures and objects for better manipulation and extension
- adjusted readability and documentation
- removed support for non-`sql` backends (for now)
- now works with `qstion` package for better filter handling

### [0.2.14] - 2024-05-27

- changed checking whether query is paginable - now only requirement is that the ordered column is not present in any nesed expression with `eq` `neq` `in_` or `nin` operator


### [0.2.13] - 2024-05-27

- now order by columns from `PaginationBuilder` class is able to recognize referenced column and return its referenced name instead of base column name

### [0.2.11] - 2024-05-27

- added support for `Decimal` type of column in `sql.SQL` backend

### [0.2.10] - 2024-05-27

- adjustment to extracting data from binary expressions: now also counts `Label` as column element

### [0.2.9] - 2024-05-21

- adjustments to removals - now accepted as list of `Removal` class

### [0.2.8] - 2024-05-21

- substitutions for reconstructing filter are now in class and are accepted as list of `Substitution` objects
- unused substitutions are now added to filters

### [0.2.6] - 2024-05-21

- added option to `PaginationBuilder` to provide `removals` as for removing fields from filter

### [0.2.5] - 2024-05-21

- removed operations as methods from `QueryBuilder` class
and rewritten them as separate classes for more flexibility and easier extension
- implemented `Paginationbuilder` class for rebuilding filter from query providing filter which can be adjusted


### [0.2.4] - 2024-05-20

- added helper method in `sql.SQL` backend - `is_query_paginable` - to check if query is paginable (for pointer based pagination) - based on selected columns

### [0.2.3] - 2024-05-07

- Added support for parsing `datetime` and `date` objects in `sql.SQL` backend from `str` format (assuming iso-format of string)
- New class `FilterTypeParser` added to `sql.SQL` backend to return constructor for given type (e.g. `datetime`, `date`, `int`, `float`, `str`, `bool`) - now able to parse `datetime` and `date` objects from `str` format

### [0.2.2] - 2024-03-04

- Validation changes: now instead of checking whether value in filter is of instance `column.type.python_type`, it uses the given `python_type` constructor to check if the value is processable by the given type
- Operations now apply the `python_type` constructor to the value before applying the operation 


### [0.2.1] - 2024-02-26

- Added advanced tests and logging

### [0.2.0] - 2024-02-26

- Removed support for `ignore_extra_fields` and `strict` options in `sql.SQL.build` method 
- added feature for infinite nesting - using `junctions` - AND/OR operators for sql queries - allowing advanced filtering and grouped clauses
- refactored validation of filter structure and columns, and restriction models
- added base class which has to be used when creating custom restriction models

## [0.1.3] - 2024-01-30

- added option `strict` kwarg (defaults to `True`) to `sql.SQL.build` method to ignore fields in filter that don't correspond to expected `FORMAT` - does not apply to `ignore_extra_fields` option
- method `sql.SQL.validate_filter_structure` now instead of 'only validating' returns `dict` of processed filter items (because of `strict` option)

## [0.1.2] - 2024-01-29

- added option `ignore_extra_fields` kwarg(defaults to `False`) to `sql.SQL.build` method to ignore extra fields in `filters` argument when using restriction model
- method `sql.SQL.validate_filter_columns` now instead of 'only validating' returns `dict` of processed filter items (because of `ignore_extra_fields` option)

## [0.1.1] - 2024-01-25

- changed the way how `SQL` backend handles `order_by` keyword argument: now accepts `str` and `list` of `str` (instead of `dict` and `list` of `dict`) in following format options:
    - `<order>(<field>)` - order being `asc` or `desc`
    - `<order><field>` - order being `+` for `asc` and `-` for `desc`
    - `<field>.<order>` - order being `asc` or `desc``

## [0.1.0] - 2024-01-24

- added advanced validation using `pydantic` library
- added option (for `SQL`) to use restriction model (using `BaseModel` from `pydantic`) to restrict incoming filters
- added more tests

## [0.0.1] - 2023-11-06

- project created