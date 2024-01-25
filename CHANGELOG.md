# Changelog

All notable changes to [qstion](https://github.com/kajotgames/qstion) project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

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