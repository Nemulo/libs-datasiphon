# Changelog

All notable changes to [qstion](https://github.com/kajotgames/qstion) project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

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