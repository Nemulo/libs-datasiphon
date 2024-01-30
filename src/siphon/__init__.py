# TODO: Main idea:
# take dict of data (filter from qstion) and using neccesary data(objects, switchers, etc) build usable object for any
# type of database client
# 1. research database clients for python - Start with SQL - sqlalchemy supports all dialects
from . import sql, nosql, base
import typing as t

VERSION = (0, 1, 3)
__version__ = '.'.join(map(str, VERSION))


t_Database = t.TypeVar('t_Database', sql.SQL, nosql.Mongo)

__all__ = ['build', 'sql', 'nosql']


def build(filter_: dict, builder_class: t_Database, input_: t.Any) -> t.Any:
    DeprecationWarning('Use builder_class.build(input_, filter_) instead')
    return builder_class.build(input_, filter_)
