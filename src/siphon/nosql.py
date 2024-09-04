# start with mongoDB
from .base import QueryBuilder, FilterFormatError, FilterColumnError, InvalidOperatorError, InvalidValueError
import pymongo.collection as pc
import pymongo.cursor as pcur
import typing as t


# TODO implement the mongo query builder
class Mongo(QueryBuilder):
    """
    Mongo query builder
    """
