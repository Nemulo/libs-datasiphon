from sqlalchemy import Table, Select, and_ as sa_and, or_ as sa_or, asc as sa_asc, desc as sa_desc
from sqlalchemy.sql.elements import ColumnElement, UnaryExpression
import sqlalchemy.sql.operators as sql_operators
from sqlalchemy.sql.base import ColumnCollection
from qstion._struct_core import QsRoot, QsNode
import enum
import typing as t
from copy import deepcopy

from .core import _filter_core as core
from .core._exc import ColumnError, CannotAdjustExpression, FiltrationNotAllowed, InvalidValueTypeError

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


# TODO: adjust navigation in FilterExpression
# currently a bit whacky - adjust finding !! most important
# adapt other functions to work with new navigation
class FilterExpression:
    junction: Junction | None
    nested_expressions: list["FilterExpression"]
    column: ColumnElement
    operator: core.FilterOperation

    def __init__(self, column: ColumnElement, operator: core.FilterOperation):
        self.column = column
        self.operator = operator
        self.junction = None
        self.nested_expressions = []

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
        whereclause = self.produce_whereclause()
        return query.where(whereclause)

    def produce_whereclause(self) -> ColumnElement:
        if self.is_junction:
            nested_whereclauses = [expr.produce_whereclause() for expr in self.nested_expressions]
            return self.junction.value(*nested_whereclauses)
        return self.operator.evaluate(self.column)

    def add_expression(
        self, path: list[str] | str, expression: "FilterExpression", use_junction: Junction = Junction.AND
    ) -> None:
        """
        Adds a new expression to the instance.

        If path is None, the expression is added to the current instance.
        NOTE: if current instance is not a junction - implicit and junction is created if not specified what `junction` to use.
        Otherwise, the expression is added to the nested expression with omitted specified junction.
        If path is a string, it is split by "." and the expression is added to the corresponding nested expression.
        If path is a list of strings, the expression is added to the corresponding nested expression.
        also NOTE: that path is only consisting of junctions, since the column is already specified in the expression. - for navigation
        to correct nested expression.

        Args:
            path (list[str] | str | None): A path to the nested expression.
            expression (FilterExpression): A new expression to add.

        Raises:
            CannotAdjustExpression: If the path is invalid.
        """
        target_expr = self.find_expression(path)
        if target_expr is None:
            raise CannotAdjustExpression("Destination expression not found.")
        if target_expr.is_junction and target_expr.junction == use_junction:
            target_expr.nested_expressions.append(expression)
        else:
            target_copy = deepcopy(target_expr)
            target_expr.junction = use_junction
            target_expr.nested_expressions = [target_copy, expression]
            target_expr.column = None
            target_expr.operator = None

    def find_expression(self, path: list[str] | str) -> t.Union["FilterExpression", None]:
        """
        Finds an expression based on the path.

        If path is None, the current instance is returned.
        If path is a string, it is split by "." and the corresponding nested expression is returned.
        If path is a list of strings, the corresponding nested expression is returned.
        NOTE:
        path must be all - except last item - junctions
        last item can be either junction or simple expression in following format:
        either `column_name` or `column_name:operator`, or even `column_name:operator-value`

        Args:
            path (list[str] | str | None): A path to the nested expression.

        Returns:
            FilterExpression: A found expression.

        Raises:
            CannotAdjustExpression: If the path is invalid.
        """
        if not isinstance(path, list):
            path = path.split(".")
        if len(path) == 0:
            return self
        # take first element from path
        if path[0] in SqlQueryBuilder.JUNCTIONS and self.junction == Junction.from_str(path[0]):
            if len(path) == 1:
                return self
            for expr in self.nested_expressions:
                found_expr = expr.find_expression(path[1:])
                if found_expr is not None:
                    return found_expr
            return None
        elif self.column is not None:
            # try to split the last element
            column_definition = path[0].split(":")
            column_name, operator = column_definition[0], column_definition[1] if len(column_definition) > 1 else None
            op_name, op_value = operator.split("-") if operator and "-" in operator else (operator, None)
            column_match = self.column.key == column_name
            operator_match = (self.operator.filter_name == op_name) if op_name is not None else True
            value_match = (self.operator.assigned_value == op_value) if op_value is not None else True
            if column_match and operator_match and value_match:
                return self
            return None
        else:
            return None

    def replace_expression(self, path: list[str] | str, expression: "FilterExpression") -> None:
        """
        Replaces an expression based on the path.
        Contrary to `add_expression`, path can contain non-junction elements for targeting the specific simple expressions as well.
        NOTE that this simple element can be located only on the last position in the path.

        Args:
            path (list[str] | str): A path to the nested expression.
            expression (FilterExpression): An expression to replace the found one.
        """
        if not path:
            self.replace(expression)
            return
        if not isinstance(path, list):
            path = path.split(".")
        target_expr = self.find_expression(path)
        if target_expr is None:
            raise CannotAdjustExpression("Destination expression not found.")
        target_expr.replace(expression)

    def replace(self, other: "FilterExpression") -> None:
        """
        Replaces the current expression with another one.
        """
        self.junction = other.junction
        self.nested_expressions = other.nested_expressions
        self.column = other.column
        self.operator = other.operator

    def remove_expression(self, path: list[str] | str) -> None:
        """
        Works similiarly as `replace_expression`, but removes the found expression.
        """
        if not path:
            raise CannotAdjustExpression("Cannot remove the root expression.")
        if not isinstance(path, list):
            path = path.split(".")
        target_expr = self.find_expression(path)
        if target_expr is None:
            raise CannotAdjustExpression("Destination expression not found.")
        parent_expr = self.find_expression(path[:-1])
        parent_expr.nested_expressions.remove(target_expr)

    def normalize(self) -> None:
        """
        Normalizes filter expression by removing redundant junctions,
        and merging simple expressions with same column key into junction.
        """
        # traverse from root - preorder like, except leave leaf nodes be
        if self.is_junction:
            for expr in self.nested_expressions:
                expr.normalize()
        else:
            # simple expression
            return
        # 1. remove empty junctions
        self.nested_expressions = [
            expr for expr in self.nested_expressions if not expr.is_junction or expr.nested_expressions
        ]
        # done

    def dump(self):
        """
        Dumps the expression into a dictionary.
        """
        if self.is_junction:
            # after normalization, there should be no junctions with only one nested expression
            # e.g recursively dump nested expressions and their name should be unique
            data = {}
            for expr in self.nested_expressions:
                # junctions have to be array like - so we have to wrap them into a list
                dump_result = expr.dump()  # should be dictionary with exactly one key
                for key, value in dump_result.items():
                    if key not in data:
                        data[key] = value
                    elif key in data and key not in SqlQueryBuilder.JUNCTIONS:
                        data[key].update(value)
                    else:
                        data[key] = FilterExpression.merge_dumps(data[key], value)
            return {self.junction.name.lower(): data}
        else:
            # simple expression
            return {self.column.key: self.operator.dump()}

    @staticmethod
    def merge_dumps(current: dict, incoming: dict) -> dict:
        """
        Merges two dumps into one.
        """
        if not FilterExpression.is_array_like_dict(current):
            current = FilterExpression.to_array_like_dict(current)
        next_index = max(current.keys()) + 1
        current[next_index] = incoming
        return current

    @staticmethod
    def is_array_like_dict(item: dict):
        indexes = all(isinstance(key, int) for key in item.keys())
        nested_items = all(isinstance(value, dict) for value in item.values())
        return indexes and nested_items

    @staticmethod
    def to_array_like_dict(item: dict):
        return {0: item}


class SqlKeywordFilter:
    """
    A class that represents a keyword filtering in SQL.
    """

    limit: int | None
    offset: int | None
    order_by: list[UnaryExpression]

    def __init__(self):
        self.limit = None
        self.offset = None
        self.order_by = []

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
        self.order_by.extend(columns)

    def apply(self, query: Select) -> Select:
        if self.limit is not None:
            query = query.limit(self.limit)
        if self.offset is not None:
            query = query.offset(self.offset)
        if self.order_by is not None:
            query = query.order_by(*self.order_by)
        return query

    def to_dict(self) -> dict[str, t.Any]:
        order_by_direction = {
            sql_operators.asc_op: "+",
            sql_operators.desc_op: "-",
        }
        data = {}
        if self.limit is not None:
            data["limit"] = self.limit
        if self.offset is not None:
            data["offset"] = self.offset
        if self.order_by:
            # parse always from `UnaryExpression` to string
            # use sign notation for direction
            data["order_by"] = (
                [f"{order_by_direction[c.modifier]}{c.element.key}" for c in self.order_by]
                if len(self.order_by) > 1
                else f"{order_by_direction[self.order_by[0].modifier]}{self.order_by[0].element.key}"
            )
        return data


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
        parent_junction: Junction = Junction.AND,
    ) -> FilterExpression | list[FilterExpression]:
        """
        Creates a filter expression object based on a QsNode which is assumed to be already validated.
        """
        if node.key in self.KEYWORDS:
            keyword, value = self.process_keyword_node(node, columns)
            keyword_filter.add_keyword(keyword, value)
            return None
        if node.key in self.JUNCTIONS:
            # NOTE: if value of this node is array like dict - it indicates that there are multiple junctions
            # with same name (which cannot be represented in dict format in other way than array-like dict)
            if node.is_array_branch:
                return [
                    FilterExpression.joined_expressions(
                        Junction.from_str(node.key),
                        self.create_filter_expression(
                            child, columns, keyword_filter, parent_column, restrictions=restrictions
                        ),
                    )
                    for child in node.value
                ]
            nested_expressions = []
            for child in node.value:
                expr = self.create_filter_expression(
                    child,
                    columns,
                    keyword_filter,
                    parent_column,
                    restrictions=restrictions,
                    parent_junction=Junction.from_str(node.key),
                )
                if isinstance(expr, list):
                    nested_expressions.extend(expr)
                else:
                    nested_expressions.append(expr)

            return FilterExpression.joined_expressions(
                Junction.from_str(node.key),
                *nested_expressions,
            )
        # check for multi-junction in array-like dict format
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
                nested_expressions = [
                    self.create_filter_expression(child, columns, keyword_filter, node.key, restrictions=restrictions)
                    for child in node.value
                ]
                return FilterExpression.joined_expressions(
                    parent_junction,
                    *nested_expressions,
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


def reconstruct_filtering(
    expression: FilterExpression, keywords: SqlKeywordFilter, as_obj: bool = False
) -> dict | QsRoot:
    """
    Reconstructs filtering object from a dictionary.
    """
    # 1. iterate over expression and dump it into a dictionary
    # 2. iterate over keywords and dump them into a dictionary
    if expression is not None:
        expression.normalize()
        filter_dump = expression.dump()
    else:
        filter_dump = {}
    keyword_dump = keywords.to_dict()
    filter_dump.update(keyword_dump)
    root = QsRoot()
    for key, value in filter_dump.items():
        node = QsNode.load_from_dict(key, value, parse_array=True)
        root.add_child(node)
    if as_obj:
        return root
    return root.to_dict()
