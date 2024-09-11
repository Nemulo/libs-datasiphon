import unittest
import sys
import data
import sqlalchemy as sa
from copy import deepcopy

sys.path.append(".")


class SQLTest(unittest.TestCase):

    def test_incorrect_formats(self):
        import src.datasiphon as ds
        from src.datasiphon import _exc as core_exc

        # set up builder
        builder = ds.SqlQueryBuilder(
            {
                "tt": data.test_table,
                "st": data.secondary_test,
                "tts": data.table_with_time_stamp,
            }
        )

        # keyword with invalid values - limit not int-like
        f_ = {"limit": "john"}

        with self.assertRaises(core_exc.InvalidValueTypeError):
            builder.build(data.basic_enum_select, f_)

        # keyword with invalid values - offset not int-like
        f_ = {"offset": "john"}

        with self.assertRaises(core_exc.InvalidValueTypeError):
            builder.build(data.basic_enum_select, f_)

        # keyword with invalid values - order incorrect format
        f_ = {"order_by": "john"}

        with self.assertRaises(core_exc.BadFormatError):
            builder.build(data.basic_enum_select, f_)

        f_ = {"order_by": ["john", "doe"]}
        with self.assertRaises(core_exc.BadFormatError):
            builder.build(data.basic_enum_select, f_)

        # bad filter format - column without operator
        f_ = {"name": "john"}
        with self.assertRaises(core_exc.InvalidFilteringStructureError):
            builder.build(data.basic_enum_select, f_)

        # bad filter format - column with unknown operator
        f_ = {"name": {"unknown": "john"}}
        with self.assertRaises(core_exc.InvalidFilteringStructureError):
            builder.build(data.basic_enum_select, f_)

        # operator without column
        f_ = {"eq": "john"}
        with self.assertRaises(core_exc.InvalidFilteringStructureError):
            builder.build(data.basic_enum_select, f_)

    def test_basic_select(self):
        import src.datasiphon as ds
        from src.datasiphon import _exc as core_exc

        # set up builder
        builder = ds.SqlQueryBuilder(
            {
                "tt": data.test_table,
                "st": data.secondary_test,
                "tts": data.table_with_time_stamp,
            }
        )

        # test filter with non-existent column
        f_ = {"country": {"eq": "USA"}}

        with self.assertRaises(core_exc.ColumnError):
            builder.build(data.basic_enum_select, f_)

        # test with no filter
        f_ = {}
        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(data.basic_enum_select),
        )

        # simple filter
        f_ = {"name": {"eq": "John"}}
        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(data.basic_enum_select.where(data.test_table.c.name == "John")),
        )

        # multiple filters
        f_ = {"name": {"eq": "John"}, "age": {"gt": 20}}
        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(
                data.basic_enum_select.where(
                    sa.and_(
                        data.test_table.c.name == "John",
                        data.test_table.c.age > 20,
                    )
                )
            ),
        )

    def test_select_keywords(self):
        import src.datasiphon as ds

        # set up builder
        builder = ds.SqlQueryBuilder(
            {
                "tt": data.test_table,
                "st": data.secondary_test,
                "tts": data.table_with_time_stamp,
            }
        )

        # test limit
        f_ = {"limit": 10}
        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(data.basic_enum_select.limit(10)),
        )

        # test offset
        f_ = {"offset": 10}
        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(data.basic_enum_select.offset(10)),
        )

        # test order by - multiple formats available
        f_ = {"order_by": "+name"}
        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(data.basic_enum_select.order_by(data.test_table.c.name.asc())),
        )

        f_ = {"order_by": "-name"}
        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(data.basic_enum_select.order_by(data.test_table.c.name.desc())),
        )

        f_ = {"order_by": "asc(name)"}
        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(data.basic_enum_select.order_by(data.test_table.c.name.asc())),
        )

        f_ = {"order_by": "desc(name)"}
        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(data.basic_enum_select.order_by(data.test_table.c.name.desc())),
        )

        f_ = {"order_by": "name.asc"}
        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(data.basic_enum_select.order_by(data.test_table.c.name.asc())),
        )

        f_ = {"order_by": "name.desc"}
        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(data.basic_enum_select.order_by(data.test_table.c.name.desc())),
        )

        f_ = {"order_by": ["+name", "-age"]}
        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(data.basic_enum_select.order_by(data.test_table.c.name.asc(), data.test_table.c.age.desc())),
        )

    def test_select_operators(self):
        import src.datasiphon as ds
        from src.datasiphon import _exc as core_exc

        # set up builder
        builder = ds.SqlQueryBuilder(
            {
                "tt": data.test_table,
                "st": data.secondary_test,
                "tts": data.table_with_time_stamp,
            }
        )

        # test eq
        f_ = {"name": {"eq": "John"}}
        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(data.basic_enum_select.where(data.test_table.c.name == "John")),
        )

        # test ne
        f_ = {"name": {"ne": "John"}}
        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(data.basic_enum_select.where(data.test_table.c.name != "John")),
        )

        # test gt
        f_ = {"age": {"gt": 20}}
        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(data.basic_enum_select.where(data.test_table.c.age > 20)),
        )

        # test ge
        f_ = {"age": {"ge": 20}}
        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(data.basic_enum_select.where(data.test_table.c.age >= 20)),
        )

        # test lt
        f_ = {"age": {"lt": 20}}
        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(data.basic_enum_select.where(data.test_table.c.age < 20)),
        )

        # test le
        f_ = {"age": {"le": 20}}
        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(data.basic_enum_select.where(data.test_table.c.age <= 20)),
        )

        # test in_
        # if not list - should raise error
        with self.assertRaises(core_exc.InvalidValueTypeError):
            f_ = {"name": {"in_": "John"}}
            builder.build(data.basic_enum_select, f_)

        f_ = {"name": {"in_": ["John", "Doe"]}}

        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(data.basic_enum_select.where(data.test_table.c.name.in_(["John", "Doe"]))),
        )

        # test not_in
        # if not list - should raise error
        with self.assertRaises(core_exc.InvalidValueTypeError):
            f_ = {"name": {"nin": "John"}}
            builder.build(data.basic_enum_select, f_)

        f_ = {"name": {"nin": ["John", "Doe"]}}

        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(data.basic_enum_select.where(data.test_table.c.name.notin_(["John", "Doe"]))),
        )

    def test_advanced_selects(self):
        import src.datasiphon as ds
        from src.datasiphon import _exc as core_exc

        # prepare builder
        builder = ds.SqlQueryBuilder(
            {
                "tt": data.test_table,
                "st": data.secondary_test,
                "tts": data.table_with_time_stamp,
            }
        )
        combined_select = data.combined_enum_select
        # test using filter on column from first table
        f_ = {"name": {"eq": "John"}}
        self.assertEqual(
            str(builder.build(combined_select, f_)),
            str(combined_select.where(data.test_table.c.name == "John")),
        )
        # test using filter on column from second table
        f_ = {"primary_id": {"eq": 1}}
        self.assertEqual(
            str(builder.build(combined_select, f_)),
            str(combined_select.where(data.secondary_test.c.primary_id == 1)),
        )
        # test using filter on both tables
        f_ = {"name": {"eq": "John"}, "primary_id": {"eq": 1}}
        self.assertEqual(
            str(builder.build(combined_select, f_)),
            str(
                combined_select.where(
                    sa.and_(
                        data.test_table.c.name == "John",
                        data.secondary_test.c.primary_id == 1,
                    )
                )
            ),
        )

        # test partial select dereferencing column that is not in the select
        f_ = {"tt.id": {"eq": 1}}
        self.assertEqual(
            str(builder.build(data.partial_select, f_)),
            str(data.partial_select.where(data.test_table.c.id == 1)),
        )
        # test partial combined select dereferencing columns from both tables that are not in the select
        f_ = {"tt.id": {"eq": 1}, "st.primary_id": {"eq": 1}}
        self.assertEqual(
            str(builder.build(data.partial_combined_select, f_)),
            str(
                data.partial_combined_select.where(
                    sa.and_(
                        data.test_table.c.id == 1,
                        data.secondary_test.c.primary_id == 1,
                    )
                )
            ),
        )
        # bad dereferencing
        f_ = {"tt.unknown_column": {"eq": 1}}
        with self.assertRaises(core_exc.ColumnError):
            builder.build(data.partial_select, f_)

        # test labeled select
        f_ = {"name": {"eq": "John"}}
        with self.assertRaises(core_exc.ColumnError):
            builder.build(data.labeled_select, f_)

        # set filter to correct label
        # NOTE: using literal_binds=True to better compare output, otherwise it would be a bit
        # -different due to the way SQLAlchemy handles literals - :name_1 vs :param_1
        f_ = {"tt_name": {"eq": "John"}}
        self.assertEqual(
            str(builder.build(data.labeled_select, f_).compile(compile_kwargs={"literal_binds": True})),
            str(
                data.labeled_select.where(data.test_table.c.name == "John").compile(
                    compile_kwargs={"literal_binds": True}
                )
            ),
        )

        # test labeled combined select
        f_ = {"tt_name": {"eq": "John"}, "ST_ID": {"eq": 1}}
        self.assertEqual(
            str(builder.build(data.labeled_combined_select, f_).compile(compile_kwargs={"literal_binds": True})),
            str(
                data.labeled_combined_select.where(
                    sa.and_(
                        data.test_table.c.name == "John",
                        data.secondary_test.c.id == 1,
                    )
                ).compile(compile_kwargs={"literal_binds": True})
            ),
        )

    def test_filter_restrictions(self):
        import src.datasiphon as ds
        from src.datasiphon import _exc as core_exc

        # prepare builder
        builder = ds.SqlQueryBuilder(
            {
                "tt": data.test_table,
                "st": data.secondary_test,
                "tts": data.table_with_time_stamp,
            }
        )

        # test simple filter, no restrictions
        f_ = {"name": {"eq": "John"}}
        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(data.basic_enum_select.where(data.test_table.c.name == "John")),
        )

        # test simple filter on column that is not restricted, but restrictions are provided
        f_ = {"name": {"eq": "John"}}
        age_restriction = ds.ColumnFilterRestriction.from_dict("age", {"eq": ds.AnyValue})
        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_, age_restriction)),
            str(data.basic_enum_select.where(data.test_table.c.name == "John")),
        )

        # test simple filter on column that is restricted
        f_ = {"age": {"eq": 20}}
        with self.assertRaises(core_exc.FiltrationNotAllowed):
            builder.build(data.basic_enum_select, f_, age_restriction)

        # restrict age column but on different operation
        f_ = {"age": {"gt": 20}}
        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_, age_restriction)),
            str(data.basic_enum_select.where(data.test_table.c.age > 20)),
        )

        # restrict age column on same operation, but on specific value
        f_ = {"age": {"eq": 20}}
        age_restriction = ds.ColumnFilterRestriction.from_dict("age", {"eq": 20})
        with self.assertRaises(core_exc.FiltrationNotAllowed):
            builder.build(data.basic_enum_select, f_, age_restriction)

        # different value should work
        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(data.basic_enum_select.where(data.test_table.c.age == 21)),
        )

    def test_junctions(self):
        import src.datasiphon as ds
        from src.datasiphon import _exc as core_exc

        # prepare builder
        builder = ds.SqlQueryBuilder(
            {
                "tt": data.test_table,
                "st": data.secondary_test,
                "tts": data.table_with_time_stamp,
            }
        )

        # test no junction
        f_ = {"name": {"eq": "John"}}
        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(data.basic_enum_select.where(data.test_table.c.name == "John")),
        )
        # test one simple junction above column name
        f_ = {"and": {"name": {"eq": "John"}, "age": {"gt": 20}}}
        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(
                data.basic_enum_select.where(
                    sa.and_(
                        data.test_table.c.name == "John",
                        data.test_table.c.age > 20,
                    )
                )
            ),
        )
        f_ = {"or": {"name": {"eq": "John"}, "age": {"gt": 20}}}
        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(
                data.basic_enum_select.where(
                    sa.or_(
                        data.test_table.c.name == "John",
                        data.test_table.c.age > 20,
                    )
                )
            ),
        )
        # test multiple junctions above column name
        f_ = {
            "or": {"name": {"eq": "John"}, "and": {"age": {"gt": 20}, "created_at": {"gt": "2020-01-01"}}},
            "is_active": {"eq": True},
        }
        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(
                data.basic_enum_select.where(
                    sa.and_(
                        sa.or_(
                            data.test_table.c.name == "John",
                            sa.and_(
                                data.test_table.c.age > 20,
                                data.test_table.c.created_at > "2020-01-01",
                            ),
                        ),
                        data.test_table.c.is_active == True,
                    )
                )
            ),
        )
        # test multiple but obsolete junctions above column name
        # - this filter is equivalent to
        # {
        #     "or": {"name": {"eq": "John"}, "age": {"gt": 20}
        # },
        # since every junction above does not have any effect
        f_ = {"or": {"and": {"or": {"name": {"eq": "John"}, "age": {"gt": 20}}}}}
        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(
                data.basic_enum_select.where(
                    sa.or_(
                        data.test_table.c.name == "John",
                        data.test_table.c.age > 20,
                    )
                )
            ),
        )
        # test junction below column name
        f_ = {"name": {"and": {"eq": "John", "ne": "Doe"}}}
        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(
                data.basic_enum_select.where(
                    sa.and_(
                        data.test_table.c.name == "John",
                        data.test_table.c.name != "Doe",
                    )
                )
            ),
        )
        # test multiple junctions below column name
        f_ = {"name": {"or": {"and": {"eq": "John", "ne": "Doe"}, "eq": "Doe"}}}
        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(
                data.basic_enum_select.where(
                    sa.or_(
                        sa.and_(
                            data.test_table.c.name == "John",
                            data.test_table.c.name != "Doe",
                        ),
                        data.test_table.c.name == "Doe",
                    )
                )
            ),
        )
        # test multiple but obsolete junctions below column name
        # - this filter is equivalent to
        # {
        #     "name": {"or": {"eq": "John", "ne": "Doe"}}
        # },
        # since every junction below does not have any effect
        f_ = {"name": {"and": {"or": {"and": {"or": {"eq": "John", "ne": "Doe"}}}}}}
        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(
                data.basic_enum_select.where(
                    sa.or_(
                        data.test_table.c.name == "John",
                        data.test_table.c.name != "Doe",
                    )
                )
            ),
        )

        # test multiple combined junctions
        f_ = {
            "or": {
                "name": {"eq": "John"},
                "and": {
                    "age": {"gt": 20},
                    "or": {"is_active": {"eq": True}, "created_at": {"gt": "2020-01-01"}},
                },
                "or": {"name": {"eq": "Doe"}, "age": {"lt": 20}},
            }
        }
        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(
                data.basic_enum_select.where(
                    sa.or_(
                        data.test_table.c.name == "John",
                        sa.and_(
                            data.test_table.c.age > 20,
                            sa.or_(
                                data.test_table.c.is_active == True,
                                data.test_table.c.created_at > "2020-01-01",
                            ),
                        ),
                        sa.or_(
                            data.test_table.c.name == "Doe",
                            data.test_table.c.age < 20,
                        ),
                    )
                )
            ),
        )

    # NOTE: special input types such as datetime, date, time, etc. are supported in string format
    # and handled by SQLAlchemy, so no need to test them here

    def test_find_expression_in_filter(self):
        import src.datasiphon as ds
        from src.datasiphon import _exc as core_exc
        from src.datasiphon import sql_filter as sqlf

        # prepare builder
        builder = ds.SqlQueryBuilder(
            {
                "tt": data.test_table,
                "st": data.secondary_test,
                "tts": data.table_with_time_stamp,
            }
        )
        query_cols = ds.SqlQueryBuilder.extract_columns(data.basic_enum_select)
        # create complex expression
        controll_expr, _ = builder.create_filter(
            {
                "and": {
                    "name": {"eq": "John"},
                    "age": {"gt": 20},
                },
                "or": {
                    "age": {"lt": 10},
                    "and": {
                        "is_active": {"eq": True},
                        "created_at": {"gt": "2020-01-01"},
                    },
                    "name": {"eq": "Doe"},
                },
            },
            query_cols,
        )
        controll_copy = deepcopy(controll_expr)

        root = controll_expr.find_expression([])
        # verify structure
        match root:
            case sqlf.FilterExpression(
                junction=sqlf.Junction.AND,
                column=None,
                operator=None,
                nested_expressions=[
                    sqlf.FilterExpression(
                        junction=sqlf.Junction.AND,
                        column=None,
                        operator=None,
                        nested_expressions=[
                            sqlf.FilterExpression(
                                junction=None,
                                column=_,
                                operator=sqlf.SQLEq(
                                    filter_name="eq",
                                    assigned_value="John",
                                ),
                                nested_expressions=[],
                            ),
                            sqlf.FilterExpression(
                                junction=None,
                                column=_,
                                operator=sqlf.SQLGt(
                                    filter_name="gt",
                                    assigned_value=20,
                                ),
                                nested_expressions=[],
                            ),
                        ],
                    ),
                    sqlf.FilterExpression(
                        junction=sqlf.Junction.OR,
                        column=None,
                        operator=None,
                        nested_expressions=[
                            sqlf.FilterExpression(
                                junction=None,
                                column=_,
                                operator=sqlf.SQLLt(
                                    filter_name="lt",
                                    assigned_value=10,
                                ),
                                nested_expressions=[],
                            ),
                            sqlf.FilterExpression(
                                junction=sqlf.Junction.AND,
                                column=None,
                                operator=None,
                                nested_expressions=[
                                    sqlf.FilterExpression(
                                        junction=None,
                                        column=_,
                                        operator=sqlf.SQLEq(
                                            filter_name="eq",
                                            assigned_value=True,
                                        ),
                                        nested_expressions=[],
                                    ),
                                    sqlf.FilterExpression(
                                        junction=None,
                                        column=_,
                                        operator=sqlf.SQLGt(
                                            filter_name="gt",
                                            assigned_value="2020-01-01",
                                        ),
                                        nested_expressions=[],
                                    ),
                                ],
                            ),
                            sqlf.FilterExpression(
                                junction=None,
                                column=_,
                                operator=sqlf.SQLEq(
                                    filter_name="eq",
                                    assigned_value="Doe",
                                ),
                                nested_expressions=[],
                            ),
                        ],
                    ),
                ],
            ):
                pass
            case _:
                self.fail("Incorrect structure")

        # test finding expressions
        # find first `and` junction
        expr = controll_copy.find_expression(["and"])
        match expr:
            case sqlf.FilterExpression(
                junction=sqlf.Junction.AND,
                column=None,
                operator=None,
                nested_expressions=[
                    sqlf.FilterExpression(
                        junction=None,
                        column=_,
                        operator=sqlf.SQLEq(
                            filter_name="eq",
                            assigned_value="John",
                        ),
                        nested_expressions=[],
                    ),
                    sqlf.FilterExpression(
                        junction=None,
                        column=_,
                        operator=sqlf.SQLGt(
                            filter_name="gt",
                            assigned_value=20,
                        ),
                        nested_expressions=[],
                    ),
                ],
            ):
                pass
            case _:
                self.fail("Incorrect structure")

        # find first `or` junction
        expr = controll_copy.find_expression(["or"])

        match expr:
            case sqlf.FilterExpression(
                junction=sqlf.Junction.OR,
                column=None,
                operator=None,
                nested_expressions=[
                    sqlf.FilterExpression(
                        junction=None,
                        column=_,
                        operator=sqlf.SQLLt(
                            filter_name="lt",
                            assigned_value=10,
                        ),
                        nested_expressions=[],
                    ),
                    sqlf.FilterExpression(
                        junction=sqlf.Junction.AND,
                        column=None,
                        operator=None,
                        nested_expressions=[
                            sqlf.FilterExpression(
                                junction=None,
                                column=_,
                                operator=sqlf.SQLEq(
                                    filter_name="eq",
                                    assigned_value=True,
                                ),
                                nested_expressions=[],
                            ),
                            sqlf.FilterExpression(
                                junction=None,
                                column=_,
                                operator=sqlf.SQLGt(
                                    filter_name="gt",
                                    assigned_value="2020-01-01",
                                ),
                                nested_expressions=[],
                            ),
                        ],
                    ),
                    sqlf.FilterExpression(
                        junction=None,
                        column=_,
                        operator=sqlf.SQLEq(
                            filter_name="eq",
                            assigned_value="Doe",
                        ),
                        nested_expressions=[],
                    ),
                ],
            ):
                pass
            case _:
                self.fail("Incorrect structure")

        # find `name` in `and` junction
        expr = controll_copy.find_expression(["and", "name"])
        match expr:
            case sqlf.FilterExpression(
                junction=None,
                column=_,
                operator=sqlf.SQLEq(
                    filter_name="eq",
                    assigned_value="John",
                ),
                nested_expressions=[],
            ):
                pass
            case _:
                self.fail("Incorrect structure")

        # find nonexistent expression
        expr = controll_copy.find_expression(["and", "is_active"])
        self.assertIsNone(expr)

        # find name:eq in `and` junction
        expr = controll_copy.find_expression(["and", "name:eq"])

        match expr:
            case sqlf.FilterExpression(
                junction=None,
                column=_,
                operator=sqlf.SQLEq(
                    filter_name="eq",
                    assigned_value="John",
                ),
                nested_expressions=[],
            ):
                pass
            case _:
                self.fail("Incorrect structure")

        # find name:lt in `and` junction - should return None
        expr = controll_copy.find_expression(["and", "name:lt"])
        self.assertIsNone(expr)

        # find name:eq-John in `and` junction
        expr = controll_copy.find_expression(["and", "name:eq-John"])

        match expr:
            case sqlf.FilterExpression(
                junction=None,
                column=_,
                operator=sqlf.SQLEq(
                    filter_name="eq",
                    assigned_value="John",
                ),
                nested_expressions=[],
            ):
                pass
            case _:
                self.fail("Incorrect structure")

        # find name:eq-Doe in `or` junction
        expr = controll_copy.find_expression(["and", "name:eq-Doe"])
        self.assertIsNone(expr)

        # find non existent nesting
        expr = controll_copy.find_expression(["and", "and"])
        self.assertIsNone(expr)

        # find deeper nesting
        expr = controll_copy.find_expression(["or", "and", "is_active:eq"])

        match expr:
            case sqlf.FilterExpression(
                junction=None,
                column=_,
                operator=sqlf.SQLEq(
                    filter_name="eq",
                    assigned_value=True,
                ),
                nested_expressions=[],
            ):
                pass
            case _:
                self.fail("Incorrect structure")

    def test_add_expression_to_filter(self):
        import src.datasiphon as ds
        from src.datasiphon.core import _exc as core_exc
        from src.datasiphon import sql_filter as sqlf

        # prepare builder
        builder = ds.SqlQueryBuilder(
            {
                "tt": data.test_table,
                "st": data.secondary_test,
                "tts": data.table_with_time_stamp,
            }
        )
        query_cols = ds.SqlQueryBuilder.extract_columns(data.basic_enum_select)

        # create simple expression and generatively add expressions to it
        controll_expr, _ = builder.create_filter(
            {
                "age": {"gt": 20},
            },
            query_cols,
        )

        # create simple `name` expression
        name_expr = sqlf.FilterExpression(
            column=query_cols["name"],
            operator=sqlf.SQLEq(
                value="John",
            ),
        )

        controll_copy = deepcopy(controll_expr)
        # try to add `name` expression to `age` expression - should raise error
        # since age is root expression
        with self.assertRaises(core_exc.CannotAdjustExpression):
            controll_copy.add_expression(["name"], name_expr)

        # add `name` expression to root expression
        controll_copy.add_expression([], name_expr)
        # verify structure
        match controll_copy:
            case sqlf.FilterExpression(
                junction=sqlf.Junction.AND,
                column=None,
                operator=None,
                nested_expressions=[
                    sqlf.FilterExpression(
                        junction=None,
                        column=_,
                        operator=sqlf.SQLGt(
                            filter_name="gt",
                            assigned_value=20,
                        ),
                        nested_expressions=[],
                    ),
                    sqlf.FilterExpression(
                        junction=None,
                        column=_,
                        operator=sqlf.SQLEq(
                            filter_name="eq",
                            assigned_value="John",
                        ),
                        nested_expressions=[],
                    ),
                ],
            ):
                pass
            case _:
                self.fail("Incorrect structure")

        # create "or" junction expression
        or_expr = sqlf.FilterExpression.joined_expressions(
            sqlf.Junction.OR,
            sqlf.FilterExpression(
                column=query_cols["is_active"],
                operator=sqlf.SQLEq(
                    value=True,
                ),
            ),
            sqlf.FilterExpression(
                column=query_cols["created_at"],
                operator=sqlf.SQLGt(
                    value="2020-01-01",
                ),
            ),
        )

        # add it to root expression
        controll_copy.add_expression([], or_expr)
        # verify structure
        match controll_copy:
            case sqlf.FilterExpression(
                junction=sqlf.Junction.AND,
                column=None,
                operator=None,
                nested_expressions=[
                    *_,
                    sqlf.FilterExpression(
                        junction=sqlf.Junction.OR,
                        column=None,
                        operator=None,
                        nested_expressions=[
                            sqlf.FilterExpression(
                                junction=None,
                                column=_,
                                operator=sqlf.SQLEq(
                                    filter_name="eq",
                                    assigned_value=True,
                                ),
                                nested_expressions=[],
                            ),
                            sqlf.FilterExpression(
                                junction=None,
                                column=_,
                                operator=sqlf.SQLGt(
                                    filter_name="gt",
                                    assigned_value="2020-01-01",
                                ),
                                nested_expressions=[],
                            ),
                        ],
                    ),
                ],
            ):
                pass
            case _:
                self.fail("Incorrect structure")

        # add `is_active` expression to root.name expression with `or` junction
        # creating new nesting level
        controll_copy.add_expression(
            ["name"],
            sqlf.FilterExpression(
                column=query_cols["is_active"],
                operator=sqlf.SQLEq(
                    value=True,
                ),
            ),
            use_junction=sqlf.Junction.OR,
        )
        # verify structure

        match controll_copy:
            case sqlf.FilterExpression(
                junction=sqlf.Junction.AND,
                column=None,
                operator=None,
                nested_expressions=[
                    _,
                    sqlf.FilterExpression(
                        junction=sqlf.Junction.OR,
                        column=None,
                        operator=None,
                        nested_expressions=[
                            sqlf.FilterExpression(
                                junction=None,
                                column=_,
                                operator=sqlf.SQLEq(
                                    filter_name="eq",
                                    assigned_value="John",
                                ),
                                nested_expressions=[],
                            ),
                            sqlf.FilterExpression(
                                junction=None,
                                column=_,
                                operator=sqlf.SQLEq(
                                    filter_name="eq",
                                    assigned_value=True,
                                ),
                                nested_expressions=[],
                            ),
                        ],
                    ),
                    *_,
                ],
            ):
                pass
            case _:
                self.fail("Incorrect structure")

        # add `created_at` expression to root.or expression
        created_at_junction = sqlf.FilterExpression(
            column=query_cols["created_at"],
            operator=sqlf.SQLGt(
                value="2020-01-01",
            ),
        )
        controll_copy.add_expression(
            ["or"],
            created_at_junction,
        )
        # verify structure

        match controll_copy:
            case sqlf.FilterExpression(
                junction=sqlf.Junction.AND,
                column=None,
                operator=None,
                nested_expressions=[
                    _,
                    sqlf.FilterExpression(
                        junction=sqlf.Junction.OR,
                        column=None,
                        operator=None,
                        nested_expressions=[
                            sqlf.FilterExpression(
                                junction=None,
                                column=_,
                                operator=sqlf.SQLEq(
                                    filter_name="eq",
                                    assigned_value="John",
                                ),
                                nested_expressions=[],
                            ),
                            sqlf.FilterExpression(
                                junction=None,
                                column=_,
                                operator=sqlf.SQLEq(
                                    filter_name="eq",
                                    assigned_value=True,
                                ),
                                nested_expressions=[],
                            ),
                            sqlf.FilterExpression(
                                junction=None,
                                column=_,
                                operator=sqlf.SQLGt(
                                    filter_name="gt",
                                    assigned_value="2020-01-01",
                                ),
                                nested_expressions=[],
                            ),
                        ],
                    ),
                    *_,
                ],
            ):
                pass
            case _:
                self.fail("Incorrect structure")

    def test_replace_expression_in_filter(self):
        import src.datasiphon as ds
        from src.datasiphon.core import _exc as core_exc
        from src.datasiphon import sql_filter as sqlf

        # prepare builder
        builder = ds.SqlQueryBuilder(
            {
                "tt": data.test_table,
                "st": data.secondary_test,
                "tts": data.table_with_time_stamp,
            }
        )
        query_cols = ds.SqlQueryBuilder.extract_columns(data.basic_enum_select)

        # create complex expression and replace parts of it
        controll_expr, _ = builder.create_filter(
            {
                "and": {
                    "name": {"eq": "John"},
                    "age": {"gt": 20},
                },
                "or": {
                    "age": {"lt": 10},
                    "and": {
                        "is_active": {"eq": True},
                        "created_at": {"gt": "2020-01-01"},
                    },
                    "name": {"eq": "Doe"},
                },
            },
            query_cols,
        )
        controll_copy = deepcopy(controll_expr)

        # create simple `created_at` expression
        created_at_expr = sqlf.FilterExpression(
            column=query_cols["created_at"],
            operator=sqlf.SQLGt(
                value="2020-01-01",
            ),
        )
        # replace `and.name` expression with `created_at` expression
        controll_copy.replace_expression(["and", "name"], created_at_expr)
        # verify structure

        match controll_copy:
            case sqlf.FilterExpression(
                junction=sqlf.Junction.AND,
                column=None,
                operator=None,
                nested_expressions=[
                    sqlf.FilterExpression(
                        junction=sqlf.Junction.AND,
                        column=None,
                        operator=None,
                        nested_expressions=[
                            sqlf.FilterExpression(
                                junction=None,
                                column=_,
                                operator=sqlf.SQLGt(
                                    filter_name="gt",
                                    assigned_value="2020-01-01",
                                ),
                                nested_expressions=[],
                            ),
                            *_,
                        ],
                    ),
                    *_,
                ],
            ):
                pass
            case _:
                self.fail("Incorrect structure")

        # replace `or.and` branch with created_at expression
        controll_copy.replace_expression(["or", "and"], created_at_expr)
        # verify structure

        match controll_copy:
            case sqlf.FilterExpression(
                junction=sqlf.Junction.AND,
                column=None,
                operator=None,
                nested_expressions=[
                    _,
                    sqlf.FilterExpression(
                        junction=sqlf.Junction.OR,
                        column=None,
                        operator=None,
                        nested_expressions=[
                            _,
                            sqlf.FilterExpression(
                                junction=None,
                                column=_,
                                operator=sqlf.SQLGt(
                                    filter_name="gt",
                                    assigned_value="2020-01-01",
                                ),
                                nested_expressions=[],
                            ),
                            *_,
                        ],
                    ),
                ],
            ):
                pass
            case _:
                self.fail("Incorrect structure")

            # replace `or` branch with created_at expression
        controll_copy.replace_expression(["or"], created_at_expr)
        # verify structure

        match controll_copy:
            case sqlf.FilterExpression(
                junction=sqlf.Junction.AND,
                column=None,
                operator=None,
                nested_expressions=[
                    _,
                    sqlf.FilterExpression(
                        junction=None,
                        column=_,
                        operator=sqlf.SQLGt(
                            filter_name="gt",
                            assigned_value="2020-01-01",
                        ),
                        nested_expressions=[],
                    ),
                ],
            ):
                pass
            case _:
                self.fail("Incorrect structure")

        # replace root expression with created_at expression
        controll_copy.replace_expression([], created_at_expr)
        # verify structure

        match controll_copy:
            case sqlf.FilterExpression(
                junction=None,
                column=_,
                operator=sqlf.SQLGt(
                    filter_name="gt",
                    assigned_value="2020-01-01",
                ),
                nested_expressions=[],
            ):
                pass
            case _:
                self.fail("Incorrect structure")

    def test_remove_expression_from_filter(self):
        import src.datasiphon as ds
        from src.datasiphon.core import _exc as core_exc
        from src.datasiphon import sql_filter as sqlf

        # prepare builder
        builder = ds.SqlQueryBuilder(
            {
                "tt": data.test_table,
                "st": data.secondary_test,
                "tts": data.table_with_time_stamp,
            }
        )

        query_cols = ds.SqlQueryBuilder.extract_columns(data.basic_enum_select)

        # create complex expression and remove parts of it
        controll_expr, _ = builder.create_filter(
            {
                "and": {
                    "name": {"eq": "John"},
                    "age": {"gt": 20},
                },
                "or": {
                    "age": {"lt": 10},
                    "and": {
                        "is_active": {"eq": True},
                        "created_at": {"gt": "2020-01-01"},
                    },
                    "name": {"eq": "Doe"},
                },
            },
            query_cols,
        )

        controll_copy = deepcopy(controll_expr)

        # remove `and.name` expression

        controll_copy.remove_expression(["and", "name"])
        # verify structure

        match controll_copy:
            case sqlf.FilterExpression(
                junction=sqlf.Junction.AND,
                column=None,
                operator=None,
                nested_expressions=[
                    sqlf.FilterExpression(
                        junction=sqlf.Junction.AND,
                        column=None,
                        operator=None,
                        nested_expressions=[
                            sqlf.FilterExpression(
                                junction=None,
                                column=_,
                                operator=sqlf.SQLGt(
                                    filter_name="gt",
                                    assigned_value=20,
                                ),
                                nested_expressions=[],
                            ),
                        ],
                    ),
                    *_,
                ],
            ):
                pass
            case _:
                self.fail("Incorrect structure")

        # remove `or.and` expression

        controll_copy.remove_expression(["or", "and"])
        # verify structure

        match controll_copy:
            case sqlf.FilterExpression(
                junction=sqlf.Junction.AND,
                column=None,
                operator=None,
                nested_expressions=[
                    _,
                    sqlf.FilterExpression(
                        junction=sqlf.Junction.OR,
                        column=None,
                        operator=None,
                        nested_expressions=[
                            sqlf.FilterExpression(
                                junction=None,
                                column=_,
                                operator=sqlf.SQLLt(
                                    filter_name="lt",
                                    assigned_value=10,
                                ),
                                nested_expressions=[],
                            ),
                            sqlf.FilterExpression(
                                junction=None,
                                column=_,
                                operator=sqlf.SQLEq(
                                    filter_name="eq",
                                    assigned_value="Doe",
                                ),
                                nested_expressions=[],
                            ),
                        ],
                    ),
                ],
            ):
                pass
            case _:
                self.fail("Incorrect structure")

        # remove `or` expression
        controll_copy.remove_expression(["or"])
        # verify structure

        match controll_copy:
            case sqlf.FilterExpression(
                junction=sqlf.Junction.AND,
                column=None,
                operator=None,
                nested_expressions=[
                    sqlf.FilterExpression(
                        junction=sqlf.Junction.AND,
                        column=None,
                        operator=None,
                        nested_expressions=[
                            *_,
                        ],
                    ),
                ],
            ):
                pass
            case _:
                self.fail("Incorrect structure")

    def test_normalize_filter(self):
        import src.datasiphon as ds
        from src.datasiphon.core import _exc as core_exc
        from src.datasiphon import sql_filter as sqlf

        # prepare builder
        builder = ds.SqlQueryBuilder(
            {
                "tt": data.test_table,
                "st": data.secondary_test,
                "tts": data.table_with_time_stamp,
            }
        )
        query_cols = ds.SqlQueryBuilder.extract_columns(data.basic_enum_select)

        # prepare simple filter with one element, normalizable filter
        # 1. case: Junction with one element - should return the element

        controll = sqlf.FilterExpression.joined_expressions(
            sqlf.Junction.AND,
            sqlf.FilterExpression(
                column=query_cols["name"],
                operator=sqlf.SQLEq(
                    value="John",
                ),
            ),
            sqlf.FilterExpression(
                column=query_cols["age"],
                operator=sqlf.SQLGt(
                    value=20,
                ),
            ),
        )
        # remove `age` expression
        controll.remove_expression(["age"])

        controll_copy = deepcopy(controll)
        controll_copy.normalize()
        match controll_copy:
            case sqlf.FilterExpression(
                junction=None,
                column=_,
                operator=sqlf.SQLEq(
                    filter_name="eq",
                    assigned_value="John",
                ),
                nested_expressions=[],
            ):
                pass
            case _:
                self.fail("Incorrect structure")

        # mutiple nesting levels with one element
        controll = sqlf.FilterExpression.joined_expressions(
            sqlf.Junction.AND,
            sqlf.FilterExpression.joined_expressions(
                sqlf.Junction.OR,
                sqlf.FilterExpression(
                    column=query_cols["name"],
                    operator=sqlf.SQLEq(
                        value="John",
                    ),
                ),
                sqlf.FilterExpression(
                    column=query_cols["age"],
                    operator=sqlf.SQLGt(
                        value=20,
                    ),
                ),
            ),
            sqlf.FilterExpression(
                column=query_cols["is_active"],
                operator=sqlf.SQLEq(
                    value=True,
                ),
            ),
        )
        # remove `age` expression
        controll.remove_expression(["or", "age"])
        # remove `is_active` expression
        controll.remove_expression(["is_active"])

        controll_copy = deepcopy(controll)
        controll_copy.normalize()
        # verify structure

        match controll_copy:
            case sqlf.FilterExpression(
                junction=None,
                column=_,
                operator=sqlf.SQLEq(
                    filter_name="eq",
                    assigned_value="John",
                ),
                nested_expressions=[],
            ):
                pass
            case _:
                self.fail("Incorrect structure")

        # remove empty nested expressions
        controll = sqlf.FilterExpression.joined_expressions(
            sqlf.Junction.AND,
            sqlf.FilterExpression(
                column=query_cols["name"],
                operator=sqlf.SQLEq(
                    value="John",
                ),
            ),
            sqlf.FilterExpression.joined_expressions(
                sqlf.Junction.OR,
                sqlf.FilterExpression(
                    column=query_cols["age"],
                    operator=sqlf.SQLGt(
                        value=20,
                    ),
                ),
                sqlf.FilterExpression(
                    column=query_cols["is_active"],
                    operator=sqlf.SQLEq(
                        value=True,
                    ),
                ),
            ),
        )
        # remove `is_active` expression
        controll.remove_expression(["or", "is_active"])
        # remove `age` expression
        controll.remove_expression(["or", "age"])

        controll_copy = deepcopy(controll)
        controll_copy.normalize()
        # verify structure

        match controll_copy:
            case sqlf.FilterExpression(
                junction=None,
                column=_,
                operator=sqlf.SQLEq(
                    filter_name="eq",
                    assigned_value="John",
                ),
                nested_expressions=[],
            ):
                pass
            case _:
                self.fail("Incorrect structure")

    def test_reconstruct_filter(self):
        import src.datasiphon as ds
        from src.datasiphon.core import _exc as core_exc
        from src.datasiphon import sql_filter as sqlf
        from qstion._struct_core import QsRoot, QsNode

        # prepare builder
        builder = ds.SqlQueryBuilder(
            {
                "tt": data.test_table,
                "st": data.secondary_test,
                "tts": data.table_with_time_stamp,
            }
        )

        # create simple filter
        f_ = {
            "name": {"eq": "John"},
            "age": {"gt": 20},
        }
        controll_expr, keyword_filter = builder.create_filter(
            f_, ds.SqlQueryBuilder.extract_columns(data.basic_enum_select)
        )
        # reconstruct filter
        reconstructed = sqlf.reconstruct_filtering(controll_expr, keyword_filter, as_obj=True)
        # verify structure
        match reconstructed:
            case QsRoot(
                parameter_limit=_,
                children=[
                    QsNode(
                        auto_set_key=_,
                        key="and",
                        value=[
                            QsNode(
                                auto_set_key=_,
                                key="name",
                                value=[
                                    QsNode(
                                        auto_set_key=_,
                                        key="eq",
                                        value="John",
                                    ),
                                ],
                            ),
                            QsNode(
                                auto_set_key=_,
                                key="age",
                                value=[
                                    QsNode(
                                        auto_set_key=_,
                                        key="gt",
                                        value=20,
                                    ),
                                ],
                            ),
                        ],
                    )
                ],
            ):
                pass
            case _:
                self.fail("Incorrect structure")

        # test array
        f_ = {
            "name": {"in_": ["John", "Doe"]},
        }
        controll_expr, keyword_filter = builder.create_filter(
            f_, ds.SqlQueryBuilder.extract_columns(data.basic_enum_select)
        )
        # reconstruct filter
        reconstructed = sqlf.reconstruct_filtering(controll_expr, keyword_filter, as_obj=True)
        # verify structure
        match reconstructed:
            case QsRoot(
                parameter_limit=_,
                children=[
                    QsNode(
                        auto_set_key=_,
                        key="name",
                        value=[
                            QsNode(
                                auto_set_key=_,
                                key="in_",
                                value=[
                                    QsNode(
                                        auto_set_key=_,
                                        key=0,
                                        value="John",
                                    ),
                                    QsNode(
                                        auto_set_key=_,
                                        key=1,
                                        value="Doe",
                                    ),
                                ],
                            ),
                        ],
                    )
                ],
            ):
                pass
            case _:
                self.fail("Incorrect structure")

            # test nested
        f_ = {
            "and": {
                "name": {"eq": "John"},
                "or": {
                    "age": {"gt": 20},
                    "is_active": {"eq": True},
                },
            }
        }
        controll_expr, keyword_filter = builder.create_filter(
            f_, ds.SqlQueryBuilder.extract_columns(data.basic_enum_select)
        )
        # reconstruct filter
        reconstructed = sqlf.reconstruct_filtering(controll_expr, keyword_filter, as_obj=True)
        # verify structure

        match reconstructed:
            case QsRoot(
                parameter_limit=_,
                children=[
                    QsNode(
                        auto_set_key=_,
                        key="and",
                        value=[
                            QsNode(
                                auto_set_key=_,
                                key="name",
                                value=[
                                    QsNode(
                                        auto_set_key=_,
                                        key="eq",
                                        value="John",
                                    ),
                                ],
                            ),
                            QsNode(
                                auto_set_key=_,
                                key="or",
                                value=[
                                    QsNode(
                                        auto_set_key=_,
                                        key="age",
                                        value=[
                                            QsNode(
                                                auto_set_key=_,
                                                key="gt",
                                                value=20,
                                            ),
                                        ],
                                    ),
                                    QsNode(
                                        auto_set_key=_,
                                        key="is_active",
                                        value=[
                                            QsNode(
                                                auto_set_key=_,
                                                key="eq",
                                                value=True,
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    )
                ],
            ):
                pass
            case _:
                self.fail("Incorrect structure")

        # test keyword filter - limit
        f_ = {
            "name": {"eq": "John"},
            "age": {"gt": 20},
            "limit": 10,
        }
        controll_expr, keyword_filter = builder.create_filter(
            f_, ds.SqlQueryBuilder.extract_columns(data.basic_enum_select)
        )
        # reconstruct filter
        reconstructed = sqlf.reconstruct_filtering(controll_expr, keyword_filter, as_obj=True)
        # verify structure

        match reconstructed:
            case QsRoot(
                parameter_limit=_,
                children=[
                    _,
                    QsNode(
                        auto_set_key=_,
                        key="limit",
                        value=10,
                    ),
                ],
            ):
                pass
            case _:
                self.fail("Incorrect structure")

        # test keyword filter - offset
        f_ = {
            "name": {"eq": "John"},
            "age": {"gt": 20},
            "offset": 5,
        }
        controll_expr, keyword_filter = builder.create_filter(
            f_, ds.SqlQueryBuilder.extract_columns(data.basic_enum_select)
        )
        # reconstruct filter
        reconstructed = sqlf.reconstruct_filtering(controll_expr, keyword_filter, as_obj=True)
        # verify structure

        match reconstructed:
            case QsRoot(
                parameter_limit=_,
                children=[
                    _,
                    QsNode(
                        auto_set_key=_,
                        key="offset",
                        value=5,
                    ),
                ],
            ):
                pass
            case _:
                self.fail("Incorrect structure")

        # test keyword filter - order_by all formats should result in sign notation result
        f_ = {
            "name": {"eq": "John"},
            "age": {"gt": 20},
            "order_by": "asc(name)",
        }
        controll_expr, keyword_filter = builder.create_filter(
            f_, ds.SqlQueryBuilder.extract_columns(data.basic_enum_select)
        )
        # reconstruct filter
        reconstructed = sqlf.reconstruct_filtering(controll_expr, keyword_filter, as_obj=True)
        # verify structure

        match reconstructed:
            case QsRoot(
                parameter_limit=_,
                children=[
                    _,
                    QsNode(
                        auto_set_key=_,
                        key="order_by",
                        value="+name",
                    ),
                ],
            ):
                pass
            case _:
                self.fail("Incorrect structure")

        f_ = {
            "name": {"eq": "John"},
            "age": {"gt": 20},
            "order_by": "desc(name)",
        }
        controll_expr, keyword_filter = builder.create_filter(
            f_, ds.SqlQueryBuilder.extract_columns(data.basic_enum_select)
        )
        # reconstruct filter

        reconstructed = sqlf.reconstruct_filtering(controll_expr, keyword_filter, as_obj=True)
        # verify structure

        match reconstructed:
            case QsRoot(
                parameter_limit=_,
                children=[
                    _,
                    QsNode(
                        auto_set_key=_,
                        key="order_by",
                        value="-name",
                    ),
                ],
            ):
                pass
            case _:
                self.fail("Incorrect structure")

        # multiple order by
        f_ = {
            "name": {"eq": "John"},
            "age": {"gt": 20},
            "order_by": ["+name", "age.desc"],
        }
        controll_expr, keyword_filter = builder.create_filter(
            f_, ds.SqlQueryBuilder.extract_columns(data.basic_enum_select)
        )
        # reconstruct filter
        reconstructed = sqlf.reconstruct_filtering(controll_expr, keyword_filter, as_obj=True)
        # verify structure

        match reconstructed:
            case QsRoot(
                parameter_limit=_,
                children=[
                    _,
                    QsNode(
                        auto_set_key=_,
                        key="order_by",
                        value=[
                            QsNode(
                                auto_set_key=_,
                                key=0,
                                value="+name",
                            ),
                            QsNode(
                                auto_set_key=_,
                                key=1,
                                value="-age",
                            ),
                        ],
                    ),
                ],
            ):
                pass
            case _:
                self.fail("Incorrect structure")

        # reconstruct into dict
        reconstructed = sqlf.reconstruct_filtering(controll_expr, keyword_filter, as_obj=False)
        # verify structure
        self.assertDictEqual(
            reconstructed,
            {
                "and": {
                    "name": {"eq": "John"},
                    "age": {"gt": 20},
                },
                "order_by": ["+name", "-age"],
            },
        )


if __name__ == "__main__":
    unittest.main()
