import unittest
import sys
import data
from pydantic import BaseModel
import sqlalchemy as sa

sys.path.append(".")

# TODO support for ignore and strict keyword deprecated


class SQLTest(unittest.TestCase):

    def test_select_filtering(self):
        import src.siphon as ds

        # Test filtering - format
        # 1. not a select
        with self.assertRaises(ds.base.SiphonError):
            ds.sql.SQL.build(
                data.test_table,
                {"name": {"eq": "John"}},
            )

        # 2. keyword with invalid value
        with self.assertRaises(ds.sql.FilterFormatError):
            ds.sql.SQL.build(
                data.tt_select,
                {"limit": "John"},
            )

        # 3. keyword order_by with invalid value
        with self.assertRaises(ds.sql.InvalidValueError):
            ds.sql.SQL.build(
                data.tt_select,
                {"order_by": "name"},
            )

        # 5. non-keyword with invalid value
        with self.assertRaises(ds.sql.FilterFormatError):
            ds.sql.SQL.build(
                data.tt_select,
                {"name": "John"},
            )

        # 6. non-operator key

        with self.assertRaises(ds.sql.FilterFormatError):
            ds.sql.SQL.build(
                data.tt_select,
                {"name": {"invalid": "John"}},
            )

        # Test filtering - columns
        # 1. column not in select

        with self.assertRaises(ds.sql.FilterColumnError):
            ds.sql.SQL.build(
                data.tt_select,
                {"invalid": {"eq": "John"}},
            )

        # Test filtering - correct
        # 1. No filter
        self.assertEqual(
            str(ds.sql.SQL.build(data.tt_select, {})),
            str(data.tt_select),
        )

        # 2. Simple filter
        self.assertEqual(
            str(ds.sql.SQL.build(data.tt_select, {"name": {"eq": "John"}})),
            str(data.tt_select.where(data.test_table.c.name == "John")),
        )

        # 3. Multiple filters
        self.assertEqual(
            str(ds.sql.SQL.build(data.tt_select, {"name": {"eq": "John"}, "age": {"eq": 20}})),
            str(data.tt_select.where((data.test_table.c.name == "John") & (data.test_table.c.age == 20))),
        )

        # 4. keyword limit

        self.assertEqual(str(ds.sql.SQL.build(data.tt_select, {"limit": 3})), str(data.tt_select.limit(3)))

        # 5. keyword offset
        self.assertEqual(str(ds.sql.SQL.build(data.tt_select, {"offset": 3})), str(data.tt_select.offset(3)))

        # 6. keyword order_by
        self.assertEqual(
            str(ds.sql.SQL.build(data.tt_select, {"order_by": "name.desc"})),
            str(data.tt_select.order_by(data.test_table.c.name.desc())),
        )

        self.assertEqual(
            str(ds.sql.SQL.build(data.tt_select, {"order_by": "name.asc"})),
            str(data.tt_select.order_by(data.test_table.c.name.asc())),
        )

        self.assertEqual(
            str(ds.sql.SQL.build(data.tt_select, {"order_by": "+name"})),
            str(data.tt_select.order_by(data.test_table.c.name.asc())),
        )

        self.assertEqual(
            str(ds.sql.SQL.build(data.tt_select, {"order_by": "-name"})),
            str(data.tt_select.order_by(data.test_table.c.name.desc())),
        )

        self.assertEqual(
            str(ds.sql.SQL.build(data.tt_select, {"order_by": "asc(name)"})),
            str(data.tt_select.order_by(data.test_table.c.name.asc())),
        )

        self.assertEqual(
            str(ds.sql.SQL.build(data.tt_select, {"order_by": "desc(name)"})),
            str(data.tt_select.order_by(data.test_table.c.name.desc())),
        )

        # Test every operator
        # 1. eq

        self.assertEqual(
            str(ds.sql.SQL.build(data.tt_select, {"name": {"eq": "John"}})),
            str(data.tt_select.where(data.test_table.c.name == "John")),
        )

        # 2. ne
        self.assertEqual(
            str(ds.sql.SQL.build(data.tt_select, {"name": {"ne": "John"}})),
            str(data.tt_select.where(data.test_table.c.name != "John")),
        )

        # 3. gt
        self.assertEqual(
            str(ds.sql.SQL.build(data.tt_select, {"age": {"gt": 20}})),
            str(data.tt_select.where(data.test_table.c.age > 20)),
        )

        # 4. ge
        self.assertEqual(
            str(ds.sql.SQL.build(data.tt_select, {"age": {"ge": 20}})),
            str(data.tt_select.where(data.test_table.c.age >= 20)),
        )

        # 5. lt
        self.assertEqual(
            str(ds.sql.SQL.build(data.tt_select, {"age": {"lt": 20}})),
            str(data.tt_select.where(data.test_table.c.age < 20)),
        )

        # 6. le
        self.assertEqual(
            str(ds.sql.SQL.build(data.tt_select, {"age": {"le": 20}})),
            str(data.tt_select.where(data.test_table.c.age <= 20)),
        )

        # 7. in_
        self.assertEqual(
            str(ds.sql.SQL.build(data.tt_select, {"age": {"in_": [20, 21]}})),
            str(data.tt_select.where(data.test_table.c.age.in_([20, 21]))),
        )

        # 8. nin
        self.assertEqual(
            str(ds.sql.SQL.build(data.tt_select, {"age": {"nin": [20, 21]}})),
            str(data.tt_select.where(~data.test_table.c.age.in_([20, 21]))),
        )

        # test filter value is of incorrect type
        # NOTE functionality updated v 0.2.2 - will not raise error, str is convertable to int
        self.assertEqual(
            str(ds.sql.SQL.build(data.tt_select, {"age": {"eq": "20"}})),
            str(data.tt_select.where(data.test_table.c.age == 20)),
        )

    def test_advanced_select(self):
        import src.siphon as ds

        # test combined tables - should raise error since value is of type string
        # NOTE functionality updated v 0.1.0
        # NOTE functionality updated v 0.2.2 - will not raise error, int is convertable to string
        self.assertEqual(
            str(
                ds.sql.SQL.build(
                    data.st_tt_select,
                    {"value": {"in_": [1, 2, 3]}},
                )
            ),
            str(data.st_tt_select.where(data.secondary_test.c.value.in_(["1", "2", "3"]))),
        )

        # combined tables correct select
        self.assertEqual(
            str(ds.sql.SQL.build(data.st_tt_select, {"value": {"in_": ["abc", "def"]}, "name": {"eq": "John"}})),
            str(
                data.st_tt_select.where(
                    (data.secondary_test.c.value.in_(["abc", "def"])) & (data.test_table.c.name == "John")
                )
            ),
        )

        # test base table select
        self.assertEqual(
            str(ds.sql.SQL.build(data.base_select, {"name": {"eq": "John"}})),
            str(data.base_select.where(data.test_table.c.name == "John")),
        )

    def test_invalid_inputs(self):
        import src.siphon as ds

        # test invalid inputs
        # parsed dict with invalid operators
        with self.assertRaises(ds.base.SiphonError):
            ds.sql.SQL.build({"name": {"invalid": "John"}}, ds.sql.SQL, data.tt_select)

        # parsed dict which is not nested
        with self.assertRaises(ds.base.SiphonError):
            ds.sql.SQL.build({"name": "John"}, ds.sql.SQL, data.tt_select)

        # mistyped input
        with self.assertRaises(ds.base.SiphonError):
            ds.sql.SQL.build({"name[eq": "John"}, ds.sql.SQL, data.tt_select)

        # order by is not list
        with self.assertRaises(ds.sql.FilterFormatError):
            ds.sql.SQL.build(
                data.tt_select,
                {"order_by": {"name.desc": True}},
            )

        # in is not actaully a list
        with self.assertRaises(ds.sql.InvalidValueError):
            ds.sql.SQL.build(
                data.tt_select,
                {"age": {"in_": 20}},
            )

    def test_restricted_inputs(self):
        import src.siphon as ds

        # simple restriction with no operators

        class SimpleUserRestriction(ds.sql.RestrictionModel):
            name: list[str] = []

        restriction = SimpleUserRestriction()
        with self.assertRaises(ds.sql.FilterColumnError):
            ds.sql.SQL.build(data.tt_select, {"age": {"eq": 20}}, filter_model=restriction)

        self.assertEqual(
            str(ds.sql.SQL.build(data.tt_select, {"name": {"eq": "John"}}, filter_model=restriction)),
            str(data.tt_select.where(data.test_table.c.name == "John")),
        )

        self.assertEqual(
            str(ds.sql.SQL.build(data.tt_select, {"name": {"in_": ["John", "Alex"]}}, filter_model=restriction)),
            str(data.tt_select.where(data.test_table.c.name.in_(["John", "Alex"]))),
        )

        # restrictions on filters
        class BaseUserRestriction(ds.sql.RestrictionModel):
            name: list[str] = ["eq", "ne"]

        restriction = BaseUserRestriction()

        # test restricted select with single order by
        with self.assertRaises(ds.sql.FilterColumnError):
            ds.sql.SQL.build(data.tt_select, {"order_by": "name.desc"}, filter_model=restriction)

        with self.assertRaises(ds.sql.FilterColumnError):
            ds.sql.SQL.build(data.tt_select, {"age": {"eq": 20}}, filter_model=restriction)

        # test restricted select
        with self.assertRaises(ds.sql.InvalidOperatorError):
            ds.sql.SQL.build(data.tt_select, {"name": {"in_": "John"}}, filter_model=restriction)

        class AdvancedUserRestriction(ds.sql.RestrictionModel):
            name: list[str] = ["eq", "ne"]
            age: list[str] = ["eq", "ne", "in_"]
            value: list[str] = ["in_"]
            order_by: list[str] = ["name", "age"]
            limit: bool = True

        restriction = AdvancedUserRestriction()

        # test restricted select with single order by
        self.assertEqual(
            str(ds.sql.SQL.build(data.st_tt_select, {"order_by": "name.desc"}, filter_model=restriction)),
            str(data.st_tt_select.order_by(data.test_table.c.name.desc())),
        )

        # test restricted select
        self.assertEqual(
            str(ds.sql.SQL.build(data.st_tt_select, {"name": {"eq": "John"}}, filter_model=restriction)),
            str(data.st_tt_select.where(data.test_table.c.name == "John")),
        )

        # test restricted limit
        class LimitRestriction(ds.sql.RestrictionModel):
            limit: bool = False

        restriction = LimitRestriction()

        with self.assertRaises(ds.sql.FilterColumnError):
            ds.sql.SQL.build(data.tt_select, {"limit": 3}, filter_model=restriction)

        # test invalid order by column
        with self.assertRaises(ds.sql.FilterColumnError):
            ds.sql.SQL.build(data.tt_select, {"order_by": "name.desc"}, filter_model=restriction)

        class InvalidRestrictionOperators(ds.sql.RestrictionModel):
            name: list[str] = ["eq", "ne", "invalid"]

        restriction = InvalidRestrictionOperators()

        with self.assertRaises(ds.sql.InvalidOperatorError):
            ds.sql.SQL.build(data.tt_select, {"name": {"eq": "John"}}, filter_model=restriction)

        class InvalidOrderByColumns(ds.sql.RestrictionModel):
            order_by: list[str] = ["name", "invalid"]

        restriction = InvalidOrderByColumns()

        with self.assertRaises(ds.sql.InvalidRestrictionModel):
            ds.sql.SQL.build(data.tt_select, {"order_by": "name.desc"}, filter_model=restriction)

        class NonExistentCol(ds.sql.RestrictionModel):
            invalid: list[str] = ["eq", "ne"]

        restriction = NonExistentCol()

        with self.assertRaises(ds.sql.InvalidRestrictionModel):
            ds.sql.SQL.build(data.tt_select, {"invalid": {"eq": "John"}}, filter_model=restriction)

    def test_multiple_order_by(self):
        import src.siphon as ds

        # test multiple order by's
        self.assertEqual(
            str(ds.sql.SQL.build(data.tt_select, {"order_by": ["name.desc", "age.asc"]})),
            str(data.tt_select.order_by(data.test_table.c.name.desc(), data.test_table.c.age.asc())),
        )

        # test multiple order by's with invalid column
        with self.assertRaises(ds.sql.InvalidValueError):
            ds.sql.SQL.build(data.tt_select, {"order_by": ["name.desc", "invalid"]})

        # test multiple order by's with invalid operator
        with self.assertRaises(ds.sql.InvalidValueError):
            ds.sql.SQL.build(data.tt_select, {"order_by": ["name.desc", "age.invalid"]})

    def test_and_or_junctions(self):
        import src.siphon as ds

        # simple and junction
        self.assertEqual(
            str(ds.sql.SQL.build(data.tt_select, {"and": {"name": {"eq": "John"}, "age": {"eq": 20}}})),
            str(data.tt_select.where((data.test_table.c.name == "John") & (data.test_table.c.age == 20))),
        )

        # simple or junction
        self.assertEqual(
            str(ds.sql.SQL.build(data.tt_select, {"or": {"name": {"eq": "John"}, "age": {"eq": 20}}})),
            str(data.tt_select.where((data.test_table.c.name == "John") | (data.test_table.c.age == 20))),
        )

        # test stacked and junctions - which logically results in simple junction
        self.assertEqual(
            str(ds.sql.SQL.build(data.tt_select, {"and": {"and": {"name": {"eq": "John"}, "age": {"eq": 20}}}})),
            str(data.tt_select.where((data.test_table.c.name == "John") & (data.test_table.c.age == 20))),
        )

        # test stacked or junctions - which logically results in simple junction
        self.assertEqual(
            str(ds.sql.SQL.build(data.tt_select, {"or": {"or": {"name": {"eq": "John"}}}})),
            str(data.tt_select.where((data.test_table.c.name == "John"))),
        )

        # test multiple junctions on same level
        with self.assertRaises(ds.sql.FilterFormatError):
            ds.sql.SQL.build(data.tt_select, {"and": {"name": {"eq": "John"}}, "or": {"age": {"eq": 20}}})

        # test multiple junctions on same nested level
        with self.assertRaises(ds.sql.FilterFormatError):
            ds.sql.SQL.build(data.tt_select, {"name": {"and": {"eq": "John", "ne": "John"}, "or": {"age": {"eq": 20}}}})

        # test nested junction with missing column name
        with self.assertRaises(ds.sql.FilterFormatError):
            ds.sql.SQL.build(data.tt_select, {"or": {"eq": "John", "ne": "John"}, "age": {"eq": 20}})

        # test nested junction
        self.assertEqual(
            str(ds.sql.SQL.build(data.tt_select, {"name": {"or": {"eq": "John", "ne": "John"}}, "age": {"eq": 20}})),
            str(
                data.tt_select.where(
                    ((data.test_table.c.name == "John") | (data.test_table.c.name != "John"))
                    & (data.test_table.c.age == 20)
                )
            ),
        )

        # test nested single
        self.assertEqual(
            str(ds.sql.SQL.build(data.tt_select, {"name": {"or": {"eq": "John"}}})),
            str(data.tt_select.where((data.test_table.c.name == "John"))),
        )

        # test extremely nested junction
        self.assertEqual(
            str(
                ds.sql.SQL.build(
                    data.tt_select,
                    {
                        "or": {
                            "name": {"or": {"and": {"eq": "John", "ne": "John"}, "gt": "Alex"}, "eq": "John"},
                            "age": {"eq": 20},
                        }
                    },
                )
            ),
            str(
                data.tt_select.where(
                    sa.or_(
                        sa.or_(
                            sa.and_(data.test_table.c.name == "John", data.test_table.c.name != "John"),
                            data.test_table.c.name > "Alex",
                        ),
                        data.test_table.c.name == "John",
                        data.test_table.c.age == 20,
                    )
                )
            ),
        )

    def test_parse_time_stamp_from_str(self):
        import src.siphon as ds

        # test invalid time stamp
        with self.assertRaises(ds.sql.InvalidValueError):
            ds.sql.SQL.build(data.timestamp_table_select, {"created_at": {"eq": "2021-0101 12:00:00"}})

        # test valid time stamp
        self.assertEqual(
            str(ds.sql.SQL.build(data.timestamp_table_select, {"created_at": {"eq": "2021-01-01T12:00:00"}})),
            str(data.timestamp_table_select.where(data.table_with_time_stamp.c.created_at == "2021-01-01T12:00:00")),
        )

    def test_pointer_paginable_items(self):
        import src.siphon as ds
        from sqlalchemy.sql import operators

        test_query = (
            data.table_with_time_stamp.select()
            .where(
                sa.and_(
                    data.table_with_time_stamp.c.created_at >= "2021-01-01T12:00:00",
                    sa.or_(
                        data.table_with_time_stamp.c.name == "John",
                        data.table_with_time_stamp.c.name == "Alex",
                    ),
                )
            )
            .order_by(data.table_with_time_stamp.c.created_at.desc())
        )
        second_test_query = data.table_with_time_stamp.select()

        # nested clauses for pointer will not be paginable
        # NOTE CHANGED - now paginable - only condition is that the ordered column is never used in any nested clause
        self.assertTrue(ds.sql.PaginationBuilder(test_query).is_query_paginable(["created_at"]))

        # simple query will be paginable
        self.assertTrue(ds.sql.PaginationBuilder(second_test_query).is_query_paginable(["created_at"]))

        # if operator is eq or ne, it will not be paginable
        self.assertFalse(
            ds.sql.PaginationBuilder(
                second_test_query.where(data.table_with_time_stamp.c.name == "John")
            ).is_query_paginable(["name"])
        )

        self.assertFalse(
            ds.sql.PaginationBuilder(
                second_test_query.where(data.table_with_time_stamp.c.name != "John")
            ).is_query_paginable(["name"])
        )

        # if operator is one of gt, ge etc.., it will be paginable
        self.assertTrue(
            ds.sql.PaginationBuilder(
                second_test_query.where(data.table_with_time_stamp.c.name >= "John")
            ).is_query_paginable(["name"])
        )

        self.assertTrue(
            ds.sql.PaginationBuilder(
                second_test_query.where(data.table_with_time_stamp.c.name < "John")
            ).is_query_paginable(["name"])
        )

        # on single grouping, allow paginable - paginated clauses must not have eq or ne
        # if grouping with and_ : all other where clauses except the paginated ones should be eq or ne
        self.assertTrue(
            ds.sql.PaginationBuilder(
                second_test_query.where(
                    sa.or_(
                        data.table_with_time_stamp.c.name >= "John",
                        data.table_with_time_stamp.c.created_at == "2024-04-05",
                    )
                )
            ).is_query_paginable(["name"])
        )
        self.assertFalse(
            ds.sql.PaginationBuilder(
                second_test_query.where(
                    sa.or_(
                        data.table_with_time_stamp.c.name == "John",
                        data.table_with_time_stamp.c.created_at == "2024-04-05",
                    )
                ),
            ).is_query_paginable(["name"])
        )

        # test and junction
        self.assertTrue(
            ds.sql.PaginationBuilder(
                second_test_query.where(
                    sa.and_(
                        data.table_with_time_stamp.c.name >= "John",
                        data.table_with_time_stamp.c.created_at == "2024-04-05",
                    )
                )
            ).is_query_paginable(["name"])
        )

        self.assertTrue(
            ds.sql.PaginationBuilder(
                second_test_query.where(
                    sa.and_(
                        data.table_with_time_stamp.c.name >= "John",
                        data.table_with_time_stamp.c.created_at >= "2024-04-05",
                    )
                )
            ).is_query_paginable(["name"])
        )

        # test multiple order by columns
        self.assertTrue(ds.sql.PaginationBuilder(second_test_query).is_query_paginable(["name", "created_at"]))

        # test multiple order by columns with filtered query
        self.assertTrue(
            ds.sql.PaginationBuilder(
                second_test_query.where(
                    sa.and_(
                        data.table_with_time_stamp.c.name >= "John",
                        data.table_with_time_stamp.c.created_at >= "2024-04-05",
                    )
                )
            ).is_query_paginable(["created_at", "name"])
        )

        self.assertFalse(
            ds.sql.PaginationBuilder(
                second_test_query.where(
                    sa.and_(
                        data.table_with_time_stamp.c.name >= "John",
                        data.table_with_time_stamp.c.created_at == "2024-04-05",
                    )
                )
            ).is_query_paginable(["created_at", "name"])
        )

    def test_reconstruct_filter_from_clause(self):
        import src.siphon as ds

        sample_query = data.table_with_time_stamp.select().where(
            data.table_with_time_stamp.c.name.in_(["John", "Alex"])
        )

        result = ds.sql.PaginationBuilder(sample_query).reconstruct_filter()

        # verify correct result by rebuilding query from result
        self.assertEqual(
            str(ds.sql.SQL.build(data.table_with_time_stamp.select(), result)),
            str(sample_query),
        )

        second_sample_query = data.table_with_time_stamp.select().where(
            sa.and_(
                data.table_with_time_stamp.c.name == sa.bindparam("name"),
                data.table_with_time_stamp.c.created_at == sa.bindparam("created_at"),
            )
        )
        result = ds.sql.PaginationBuilder(second_sample_query).reconstruct_filter(
            bindparams={"name": "John", "created_at": "2021-01-01T12:00:00"}
        )
        self.assertEqual(
            str(ds.sql.SQL.build(data.table_with_time_stamp.select(), result)),
            str(
                data.table_with_time_stamp.select().where(
                    sa.and_(
                        data.table_with_time_stamp.c.name == "John",
                        data.table_with_time_stamp.c.created_at == "2021-01-01T12:00:00",
                    )
                )
            ),
        )

        third_sample_query = data.table_with_time_stamp.select().where(
            sa.and_(
                data.table_with_time_stamp.c.name == sa.bindparam("name"),
                data.table_with_time_stamp.c.created_at == sa.bindparam("created_at"),
                sa.or_(
                    data.table_with_time_stamp.c.name == "John",
                    data.table_with_time_stamp.c.created_at == "2022-04-05",
                ),
            )
        )

        result = ds.sql.PaginationBuilder(third_sample_query).reconstruct_filter(
            bindparams={"name": "OI", "created_at": "2021-01-01T12:00:00"}
        )
        # since name eq or name eq, it will be converted to name in
        self.assertEqual(
            str(ds.sql.SQL.build(data.table_with_time_stamp.select(), result)),
            str(
                data.table_with_time_stamp.select().where(
                    sa.and_(
                        data.table_with_time_stamp.c.name == "OI",
                        data.table_with_time_stamp.c.created_at == "2021-01-01T12:00:00",
                        sa.or_(
                            data.table_with_time_stamp.c.name == "John",
                            data.table_with_time_stamp.c.created_at == "2022-04-05",
                        ),
                    )
                )
            ),
        )

        # test reconstruct with substitution
        result = ds.sql.PaginationBuilder(second_sample_query).reconstruct_filter(
            substitution=[ds.sql.Substitution("name", "Peter", "ne")], bindparams={"created_at": "2021-01-01T12:00:00"}
        )
        self.assertEqual(
            str(ds.sql.SQL.build(data.table_with_time_stamp.select(), result)),
            str(
                data.table_with_time_stamp.select().where(
                    sa.and_(
                        data.table_with_time_stamp.c.name != "Peter",
                        data.table_with_time_stamp.c.created_at == "2021-01-01T12:00:00",
                    )
                )
            ),
        )

        # test substition on non filtered query - should add filter
        sample_query_add = data.table_with_time_stamp.select()
        result = ds.sql.PaginationBuilder(sample_query_add).reconstruct_filter(
            substitution=[ds.sql.Substitution("name", "Peter", "eq")], bindparams={"created_at": "2021-01-01T12:00:00"}
        )
        self.assertEqual(
            str(ds.sql.SQL.build(data.table_with_time_stamp.select(), result)),
            str(
                data.table_with_time_stamp.select().where(
                    data.table_with_time_stamp.c.name == "Peter",
                )
            ),
        )

        # test reconstruct with removal
        result = ds.sql.PaginationBuilder(second_sample_query).reconstruct_filter(
            removals=[ds.sql.Removal("name")], bindparams={"created_at": "2021-01-01T12:00:00"}
        )
        self.assertEqual(
            str(ds.sql.SQL.build(data.table_with_time_stamp.select(), result)),
            str(
                data.table_with_time_stamp.select().where(
                    data.table_with_time_stamp.c.created_at == "2021-01-01T12:00:00",
                )
            ),
        )

        not_affected_query = data.table_with_time_stamp.select().where(
            data.table_with_time_stamp.c.name == "John",
        )
        # test reconstruct with removal but doesnt affect anything
        result = ds.sql.PaginationBuilder(not_affected_query).reconstruct_filter(
            removals=[ds.sql.Removal("name", "gt")],
        )
        self.assertEqual(
            str(ds.sql.SQL.build(data.table_with_time_stamp.select(), result)),
            str(not_affected_query),
        )

        # test retrieve order_by
        sample_query = data.table_with_time_stamp.select().order_by(data.table_with_time_stamp.c.created_at.desc())
        result = ds.sql.PaginationBuilder(sample_query).retrieve_order_by()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], (0, "created_at"))

        # test order by with different approach
        sample_query = data.table_with_time_stamp.select().order_by(sa.desc(data.table_with_time_stamp.c.created_at))
        result = ds.sql.PaginationBuilder(sample_query).retrieve_order_by()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], (0, "created_at"))

        # test without providing direction
        sample_query = data.table_with_time_stamp.select().order_by(data.table_with_time_stamp.c.created_at)
        result = ds.sql.PaginationBuilder(sample_query).retrieve_order_by()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], (1, "created_at"))

        # test on label
        sample_query = sa.select(
            data.table_with_time_stamp.c.name.label("name_label"),
        ).order_by(sa.desc(data.table_with_time_stamp.c.name.label("name_label")))
        result = ds.sql.PaginationBuilder(sample_query).retrieve_order_by()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], (0, "name_label"))

        # NEW: now also should be able to recognize it without label
        sample_query = sa.select(
            data.table_with_time_stamp.c.name.label("name_label"),
        ).order_by(sa.desc(data.table_with_time_stamp.c.name))

        result = ds.sql.PaginationBuilder(sample_query).retrieve_order_by()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], (0, "name_label"))

        # test retrieve operation on filtered column
        # test none
        sample_query = data.table_with_time_stamp.select().where(data.table_with_time_stamp.c.name == None)
        result = ds.sql.PaginationBuilder(sample_query).retrieve_filtered_column("created_at")
        self.assertEqual(result, None)

        # test single
        sample_query = data.table_with_time_stamp.select().where(data.table_with_time_stamp.c.name == "John")
        result = ds.sql.PaginationBuilder(sample_query).retrieve_filtered_column("name")
        self.assertIsInstance(result, ds.sql.Operation)
        self.assertEqual(result.col, "name")
        self.assertEqual(result.name, "eq")

        # test on more complex query
        sample_query = data.table_with_time_stamp.select().where(
            sa.and_(
                data.table_with_time_stamp.c.name >= "John",
                data.table_with_time_stamp.c.created_at < "2021-01-01T12:00:00",
            )
        )
        result = ds.sql.PaginationBuilder(sample_query).retrieve_filtered_column("name")
        self.assertIsInstance(result, ds.sql.Operation)
        self.assertEqual(result.col, "name")
        self.assertEqual(result.name, "ge")
        result = ds.sql.PaginationBuilder(sample_query).retrieve_filtered_column("created_at")
        self.assertIsInstance(result, ds.sql.Operation)
        self.assertEqual(result.col, "created_at")
        self.assertEqual(result.name, "lt")


if __name__ == "__main__":
    unittest.main()
