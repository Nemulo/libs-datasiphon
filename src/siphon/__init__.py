from . import sql, nosql, base
import typing as t

VERSION = (0, 2, 14)
__version__ = ".".join(map(str, VERSION))


t_Database = t.TypeVar("t_Database", sql.SQL, nosql.Mongo)

__all__ = ["build", "sql", "nosql"]
