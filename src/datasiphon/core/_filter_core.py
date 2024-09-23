import typing as t
from qstion._struct_core import QsRoot, QsNode
from ._exc import InvalidValueTypeError, NoSuchOperationError, InvalidFilteringStructureError, BadFormatError
import re


def parse_order_by(order_by: str) -> tuple[int, str | list[str]]:
    """
    Parses the order by string.
    allowed formats:
    - "asc|desc(<column_name>)"
    - "+|-<column_name>"
    - "<column_name>.asc|desc"

    Args:
        order_by: Order by string.

    Returns:
        Tuple of direction and column name.
    """
    # regex pattern for parsing the order by string
    pre_pattern = r"^(asc|desc)\(([^\(\)]+)\)$"
    sign_pattern = r"^([+-])(.+)$"
    post_pattern = r"^(.+)\.(asc|desc)$"

    direction_mapping = {"asc": 1, "desc": 0, "+": 1, "-": 0}

    direction, column_name = None, None
    # check for pre-pattern
    pre_match = re.match(pre_pattern, order_by)
    if pre_match is not None:
        direction, column_name = pre_match.groups()
        return direction_mapping[direction], column_name
    # check for sign pattern
    sign_match = re.match(sign_pattern, order_by)
    if sign_match is not None:
        direction, column_name = sign_match.groups()
        return direction_mapping[direction], column_name
    # check for post-pattern
    post_match = re.match(post_pattern, order_by)
    if post_match is not None:
        column_name, direction = post_match.groups()
        return direction_mapping[direction], column_name
    raise BadFormatError(f"Invalid order by string: {order_by}")


class AnyValue:
    """
    Placeholder for any value.
    """

    pass


class FilterOperation:
    """
    Base class for all filter operations.
    """

    filter_name: str
    assigned_value: t.Any | AnyValue

    def __init__(self, value: t.Any) -> None:
        self.assigned_value = value

    @classmethod
    def generate_restriction(cls, restricted_values: t.Any = AnyValue):
        """
        Generates a restriction
        """
        return cls(restricted_values)

    def evaluate(self) -> t.Any:
        """
        Evaluates the operation.
        """
        raise NotImplementedError("The method 'evaluate' must be implemented in the derived class.")

    def __eq__(self, other: "FilterOperation") -> bool:
        return isinstance(other, type(self)) and self.assigned_value == other.assigned_value

    def dump(self) -> dict[str, t.Any]:
        """
        Dumps the operation to a dictionary.
        """
        return {self.filter_name: self.assigned_value}


# Core operations:
# eq - equals
# ne - not equals
# gt - greater than
# ge - greater than or equal to
# lt - less than
# le - less than or equal to
# in_ - in NOTE: since python has a keyword 'in', the trailing underscore is used
# nin - not in


class Equals(FilterOperation):
    """
    Filter operation for equals.
    """

    filter_name = "eq"


class NotEquals(FilterOperation):
    """
    Filter operation for not equals.
    """

    filter_name = "ne"


class GreaterThan(FilterOperation):
    """
    Filter operation for greater than.
    """

    filter_name = "gt"


class GreaterThanOrEqual(FilterOperation):
    """
    Filter operation for greater than or equal to.
    """

    filter_name = "ge"


class LessThan(FilterOperation):
    """
    Filter operation for less than.
    """

    filter_name = "lt"


class LessThanOrEqual(FilterOperation):
    """
    Filter operation for less than or equal to.
    """

    filter_name = "le"


class In(FilterOperation):
    """
    Filter operation for in.
    """

    filter_name = "in_"
    assigned_value: list | AnyValue

    def __init__(self, value: list) -> None:
        # verify that the value is a list
        if not isinstance(value, list):
            raise InvalidValueTypeError("The value for the 'in' filter operation must be a list.")
        super().__init__(value)

    @classmethod
    def generate_restriction(cls, restricted_values: list | AnyValue = AnyValue):
        """
        Generates a restriction
        """
        if restricted_values is AnyValue:
            obj = cls([])
            obj.assigned_value = AnyValue
            return obj
        else:
            return cls(restricted_values)


class NotIn(FilterOperation):
    """
    Filter operation for not in.
    """

    filter_name = "nin"

    def __init__(self, value: t.Any) -> None:
        # verify that the value is a list
        if not isinstance(value, list):
            raise InvalidValueTypeError("The value for the 'nin' filter operation must be a list.")
        super().__init__(value)

    @classmethod
    def generate_restriction(cls, restricted_values: list | AnyValue = AnyValue):
        """
        Generates a restriction
        """
        if restricted_values is AnyValue:
            obj = cls([])
            obj.assigned_value = AnyValue
            return obj
        else:
            return cls(restricted_values)


def get_operation(operation_name: str) -> FilterOperation:
    """
    Selects the appropriate operation class based on the operation name.
    """
    operation_mapping = {
        "eq": Equals,
        "ne": NotEquals,
        "gt": GreaterThan,
        "ge": GreaterThanOrEqual,
        "lt": LessThan,
        "le": LessThanOrEqual,
        "in_": In,
        "nin": NotIn,
    }
    if operation_name not in operation_mapping:
        raise NoSuchOperationError(f"No such operation: {operation_name}")
    return operation_mapping[operation_name]


class ColumnFilterRestriction:
    """
    Base class for all column filter restrictions.
    """

    name: str
    allowed_operations: list[FilterOperation]

    def __init__(self, column_name: str, *operations: FilterOperation) -> None:
        self.name = column_name
        self.allowed_operations = operations

    @classmethod
    def from_dict(cls, column_name: str, operations: dict[str, t.Any]) -> "ColumnFilterRestriction":
        operations_list = []
        for operation_name, operation_value in operations.items():
            operation = get_operation(operation_name).generate_restriction(operation_value)
            operations_list.append(operation)
        return cls(column_name, *operations_list)

    def is_filter_allowed(self, operation: FilterOperation) -> bool:
        """
        Checks if the filter operation is allowed for the column.
        """
        for allowed_operation in self.allowed_operations:
            if isinstance(operation, type(allowed_operation)):
                # optionally if operation has assigned value, check if it's the same
                if allowed_operation.assigned_value is not AnyValue:
                    if operation.assigned_value == allowed_operation.assigned_value:
                        return False
                    return True
                return False
        return True


# NOTE: is this useful in other cases except for SQL queries?


class QueryBuilder:
    """
    Base class for all query filters.
    """

    OPERATIONS = {"eq", "ne", "gt", "ge", "lt", "le", "in_", "nin"}
    JUNCTIONS = {"and", "or"}
    KEYWORDS = {"limit", "offset", "order_by"}

    table_base: dict[str, t.Any]

    def __init__(self, table_base: dict[str, t.Any]) -> None:
        self.table_base = table_base

    @staticmethod
    def verify_filtering(filtering: QsRoot) -> list[str]:
        """
        Verifies that the filtering structure is correct.
        Structural requirement:
        - Each child node must be an `expression` node - root has implicit `and` junction if there are multiple children
        - `expression` node is either a junction - key is `and`/`or` - or a restriction - key is column name
        - `restriction` node can contain either a single operation or multiple operations (implicit `and` junction)
        or junction node explicitly stating the junction type
        - in case of combining junction and restriction nodes, the implicit `and` junction is applied between those expressions
        Expression formula example:
        - E(1) and E(2) and ... and E(n) - where E(i) is an expression node - can be indefinitely nested

        Args:
            filtering: Filtering structure to be verified.

        Raises:
            InvalidFilteringStructureError: If the filtering structure is incorrect.

        Returns:
            List of column names that are used in the filtering structure.
        """
        column_names = []
        for child in filtering.children:
            resolved_columns = QueryBuilder.process_node(child)
            if resolved_columns is not None:
                column_names.extend(resolved_columns)
        return list(set(column_names))

    @staticmethod
    def process_node(node: QsNode, parent_column: str | None = None) -> list[str] | None:
        """
        Processes a single node in the filtering structure.
        Parent column serves as a reference to column used in expression and thus implies that any subsequent child
        nodes have to be either junction of operations or operations only.

        Args:
            node: Node to be processed.
            parent_column: Name of the parent column.

        Returns:
            List of column names used in the node.
        """
        # reserved keys:
        # 'and', 'or' - junctions
        # 'limit', 'offset', 'order_by' - special keys for filtering
        # operation names - filter operations
        # 1. begin with checking node type:
        # 1.1 if it's a leaf - key should be an operation name
        if node.key in QueryBuilder.KEYWORDS:
            # reserved keyword - cannot be used as an operation name
            return None
        if node.is_leaf or node.is_simple_array_branch:
            if node.key not in QueryBuilder.OPERATIONS:
                raise InvalidFilteringStructureError(f"Leaf must be operation: Unknown operation: {node.key}")
            if parent_column is None:
                raise InvalidFilteringStructureError("Leaf node must have a parent column name set.")
        else:
            # 1.2 if it's not a leaf - key can be either a junction or a column name
            # column name only if parent_column is None - meaning if parent_column is set, the key must be a junction
            if parent_column is not None:
                if node.key not in QueryBuilder.JUNCTIONS:
                    raise InvalidFilteringStructureError(
                        f"Parent column is set - <{parent_column}> - for nested node, key must be a junction."
                    )
                for child in node.value:
                    QueryBuilder.process_node(child, parent_column)
            else:
                # parent column is not set - key cannot be an operation name
                resolved_columns = []
                if node.key in QueryBuilder.OPERATIONS:
                    raise InvalidFilteringStructureError(
                        f"Parent column is not set - cannot apply operation <{node.key}>."
                    )
                if node.key in QueryBuilder.JUNCTIONS:
                    # if it's a junction - recursively process children
                    for child in node.value:
                        # either returns a list of columns or raises an exception - cannot be None
                        resolved_columns.extend(QueryBuilder.process_node(child))
                # NOTE: also, it can be multi-use of same junction in array-like format
                elif isinstance(node.key, int):
                    # key is an index - verify children - they must be either operations or junctions
                    for child in node.value:
                        resolved_columns.extend(QueryBuilder.process_node(child))
                else:
                    # key is a column name - verify children - they must be either operations or junctions
                    for child in node.value:
                        # returns either `None` or raises an exception
                        QueryBuilder.process_node(child, node.key)
                    resolved_columns.append(node.key)
                return resolved_columns

    @staticmethod
    def load_filtering(dict_filtering: dict[str, t.Any]) -> QsRoot:
        """
        Loads the filtering structure from a dictionary.
        """
        root = QsRoot()
        for key, value in dict_filtering.items():
            node = QsNode.load_from_dict(key, value)
            root.add_child(node)
        return root
