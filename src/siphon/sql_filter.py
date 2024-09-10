from .core import _filter_core as core
from .core._exc import InvalidValueTypeError, ColumnError, FiltrationNotAllowed
from sqlalchemy import Table, Select, and_ as sa_and, or_ as sa_or, asc as sa_asc, desc as sa_desc
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.base import ColumnCollection
from qstion._struct_core import QsRoot, QsNode
import enum
import typing as t

import functools


class Junction(enum.Enum):
    AND = functools.partial(sa_and)
    OR = functools.partial(sa_or)

    @classmethod
    def from_str(cls, value: str) -> "Junction":
        return cls[value.upper()]


class SQLEq(core.Equals):

    def evaluate(self, column: ColumnElement) -> ColumnElement:
        return column == self.assigned_value


class SQLNe(core.NotEquals):

    def evaluate(self, column: ColumnElement) -> ColumnElement:
        return column != self.assigned_value


class SQLGt(core.GreaterThan):

    def evaluate(self, column: ColumnElement) -> ColumnElement:
        return column > self.assigned_value


class SQLGe(core.GreaterThanOrEqual):

    def evaluate(self, column: ColumnElement) -> ColumnElement:
        return column >= self.assigned_value


class SQLLt(core.LessThan):

    def evaluate(self, column: ColumnElement) -> ColumnElement:
        return column < self.assigned_value


class SQLLe(core.LessThanOrEqual):

    def evaluate(self, column: ColumnElement) -> ColumnElement:
        return column <= self.assigned_value


class SQLIn(core.In):

    def evaluate(self, column: ColumnElement) -> ColumnElement:
        return column.in_(self.assigned_value)


class SQLNotIn(core.NotIn):

    def evaluate(self, column: ColumnElement) -> ColumnElement:
        return column.notin_(self.assigned_value)


def get_sql_operator(operator: str) -> t.Type[core.FilterOperation]:
    return {
        "eq": SQLEq,
        "ne": SQLNe,
        "gt": SQLGt,
        "ge": SQLGe,
        "lt": SQLLt,
        "le": SQLLe,
        "in_": SQLIn,
        "nin": SQLNotIn,
    }[operator]


def get_restriction(
    column_name: str, restrictions: list[core.ColumnFilterRestriction]
) -> core.ColumnFilterRestriction | None:
    for restriction in restrictions:
        if restriction.name == column_name:
            return restriction
    return None


class FilterExpression:
    junction: Junction | None
    nested_expressions: list["FilterExpression"] | None
    column: ColumnElement
    operator: core.FilterOperation

    def __init__(self, column: ColumnElement, operator: core.FilterOperation):
        self.column = column
        self.operator = operator
        self.junction = None
        self.nested_expressions = None

    @classmethod
    def joined_expressions(cls, junction: Junction, *expressions: "FilterExpression") -> "FilterExpression":
        if len(expressions) == 0:
            return None
        elif len(expressions) == 1:
            return expressions[0]
        else:
            instance = cls(None, None)
            instance.junction = junction
            instance.nested_expressions = list(expressions)
            return instance

    @property
    def is_junction(self) -> bool:
        return self.junction is not None

    def apply(self, query: Select) -> Select:
        return query.where(self.produce_whereclause())

    def produce_whereclause(self) -> ColumnElement:
        if self.is_junction:
            return self.junction.value(*[expr.produce_whereclause() for expr in self.nested_expressions])
        return self.operator.evaluate(self.column)


class SqlKeywordFilter:
    """
    A class that represents a keyword filtering in SQL.
    """

    limit: int | None
    offset: int | None
    order_by: list[ColumnElement] | None

    def __init__(self):
        self.limit = None
        self.offset = None
        self.order_by = None

    def add_keyword(self, keyword: str, value: t.Any) -> None:
        if keyword == "limit":
            self.add_limit(value)
        elif keyword == "offset":
            self.add_offset(value)
        elif keyword == "order_by":
            self.add_order_by(*value)
        else:
            raise ValueError(f"Unsupported keyword: {keyword}")

    def add_limit(self, limit: int) -> None:
        self.limit = limit

    def add_offset(self, offset: int) -> None:
        self.offset = offset

    def add_order_by(self, *columns: ColumnElement) -> None:
        self.order_by = list(columns)

    def apply(self, query: Select) -> Select:
        if self.limit is not None:
            query = query.limit(self.limit)
        if self.offset is not None:
            query = query.offset(self.offset)
        if self.order_by is not None:
            query = query.order_by(*self.order_by)
        return query


class SqlQueryBuilder(core.QueryBuilder):
    """
    A class that builds a SQL query based on a filtering object.
    Providing table base is optional, but allows for more advanced filtering.
    """

    table_base: dict[str, Table]

    def __init__(self, table_base: dict[str, Table]) -> None:
        self.table_base = table_base

    def create_filter(
        self, filtering: QsRoot | dict, query_columns: ColumnCollection, *restrictions: core.ColumnFilterRestriction
    ) -> tuple[FilterExpression, SqlKeywordFilter]:
        if not isinstance(filtering, (QsRoot, dict)):
            raise ValueError(f"Unsupported input filtering type: {type(filtering)}")
        if isinstance(filtering, dict):
            filtering = self.load_filtering(filtering)
        self.verify_filtering(filtering)
        filter_expressions = []
        keyword_filter = SqlKeywordFilter()
        for node in filtering.children:
            filter_expression = self.create_filter_expression(
                node, query_columns, keyword_filter, restrictions=restrictions
            )
            if filter_expression is not None:
                filter_expressions.append(filter_expression)
        return FilterExpression.joined_expressions(Junction.AND, *filter_expressions), keyword_filter

    def build(self, query: Select, filtering: QsRoot | dict, *restrictions: core.ColumnFilterRestriction) -> Select:
        columns = self.extract_columns(query)
        filter_expression, keyword_filter = self.create_filter(filtering, columns, *restrictions)
        query = filter_expression.apply(query) if filter_expression else query
        query = keyword_filter.apply(query)
        return query

    def create_filter_expression(
        self,
        node: QsNode,
        columns: ColumnCollection,
        keyword_filter: SqlKeywordFilter,
        parent_column: str | None = None,
        restrictions: list[core.ColumnFilterRestriction] = None,
    ) -> FilterExpression:
        """
        Creates a filter expression object based on a QsNode which is assumed to be already validated.
        """
        if node.key in self.KEYWORDS:
            keyword, value = self.process_keyword_node(node, columns)
            keyword_filter.add_keyword(keyword, value)
            return None
        if node.key in self.JUNCTIONS:
            return FilterExpression.joined_expressions(
                Junction.from_str(node.key),
                *[
                    self.create_filter_expression(
                        child, columns, keyword_filter, parent_column, restrictions=restrictions
                    )
                    for child in node.value
                ],
            )
        else:
            # if node is a leaf node, key is operator and thus expression will inherit from parent column
            # otherwise key is column name and passed as parent column
            if node.is_leaf:
                column_ref = self.resolve_column(parent_column, columns)
                operator = get_sql_operator(node.key)(node.value)
                if restrictions and (restriction := get_restriction(column_ref.key, restrictions)):
                    if not restriction.is_filter_allowed(operator):
                        raise FiltrationNotAllowed(
                            f"Filtering operation {operator.filter_name} is not allowed, either with the current value or is forbidden as whole."
                        )
                return FilterExpression(column_ref, operator)
            elif node.is_simple_array_branch:
                # in case of `in_` or `nin` operator, node is a simple array branch
                column_ref = self.resolve_column(parent_column, columns)
                operator = get_sql_operator(node.key)([child.value for child in node.value])
                return FilterExpression(column_ref, operator)
            else:
                # node is a nested node - column argument
                return FilterExpression.joined_expressions(
                    Junction.AND,
                    *[
                        self.create_filter_expression(
                            child, columns, keyword_filter, node.key, restrictions=restrictions
                        )
                        for child in node.value
                    ],
                )

    def process_keyword_node(self, keyword_node: QsNode, query_columns: ColumnCollection) -> tuple[str, t.Any]:
        if keyword_node.key == "limit":
            # node should be always a leaf node
            # value should be an integer-like value
            if not keyword_node.is_leaf:
                raise InvalidValueTypeError("Limit keyword should be a leaf node.")
            try:
                return "limit", int(keyword_node.value)
            except ValueError:
                raise InvalidValueTypeError("Limit value should be an integer-like value.")
        elif keyword_node.key == "offset":
            # node should be always a leaf node
            # value should be an integer-like value
            if not keyword_node.is_leaf:
                raise InvalidValueTypeError("Offset keyword should be a leaf node.")
            try:
                return "offset", int(keyword_node.value)
            except ValueError:
                raise InvalidValueTypeError("Offset value should be an integer-like value.")
        elif keyword_node.key == "order_by":
            # node can be either a leaf node or a simple array node
            # value(s) should have correct format see parse_order_by in `siphon._filter_core`
            if keyword_node.is_leaf:
                # single column
                direction, column_ref = core.parse_order_by(keyword_node.value)
                return "order_by", self.resolve_order_by(direction, column_ref, query_columns)
            elif keyword_node.is_simple_array_branch:
                # multiple columns
                order_by_columns = []
                for child in keyword_node.value:
                    direction, column_ref = core.parse_order_by(child.value)
                    order_by_columns.extend(self.resolve_order_by(direction, column_ref, query_columns))
                return "order_by", order_by_columns
            else:
                raise InvalidValueTypeError("Order by keyword should be either a leaf node or a simple array node.")

    def resolve_order_by(self, direction: int, column_ref: str, query_columns: ColumnCollection) -> list[ColumnElement]:
        referenced_column = self.resolve_column(column_ref, query_columns)
        if direction:
            return [sa_asc(referenced_column)]
        return [sa_desc(referenced_column)]

    def resolve_column(self, column_ref: str, query_columns: ColumnCollection) -> ColumnElement:
        if "." in column_ref:
            table_name, column_name = column_ref.split(".")
            referenced_column = self.get_base_column(table_name, column_name)
            if referenced_column is not None:
                # found correct column reference
                return referenced_column
        # column reference is not from table_base
        # try to find it in query_columns
        referenced_column = query_columns.get(column_ref)
        if referenced_column is None:
            raise ColumnError(f"Column {column_ref} not found in query columns.")
        return referenced_column

    def get_base_column(self, table: str, column: str) -> ColumnElement | None:
        if table in self.table_base:
            db_table = self.table_base[table]
            return db_table.columns.get(column)
        return None

    @staticmethod
    def extract_columns(query: Select) -> ColumnCollection:
        return query.selected_columns
