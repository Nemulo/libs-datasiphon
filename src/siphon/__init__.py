# TODO: Main idea:
# take dict of data (filter from qstion) and using neccesary data(objects, switchers, etc) build usable object for any
# type of database client
# 1. research database clients for python - Start with SQL - sqlalchemy supports all dialects
from . import sql, nosql
import typing as t
t_Database = type(sql.SQL)

def build(filter_ : dict, builder_class: t_Database, input_: t.Any) -> t.Any:
    return builder_class.build(input_, filter_)