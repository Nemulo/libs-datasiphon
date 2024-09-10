import unittest
import sys
import data
import sqlalchemy as sa

sys.path.append(".")

# TODO support for ignore and strict keyword deprecated


class SQLTest(unittest.TestCase):

    def test_incorrect_formats(self):
        import src.siphon as ds
        from src.siphon.core import _exc as core_exc

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
        import src.siphon as ds
        from src.siphon.core import _exc as core_exc

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
        import src.siphon as ds

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
        import src.siphon as ds
        from src.siphon.core import _exc as core

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
        with self.assertRaises(core.InvalidValueTypeError):
            f_ = {"name": {"in_": "John"}}
            builder.build(data.basic_enum_select, f_)

        f_ = {"name": {"in_": ["John", "Doe"]}}

        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(data.basic_enum_select.where(data.test_table.c.name.in_(["John", "Doe"]))),
        )

        # test not_in
        # if not list - should raise error
        with self.assertRaises(core.InvalidValueTypeError):
            f_ = {"name": {"nin": "John"}}
            builder.build(data.basic_enum_select, f_)

        f_ = {"name": {"nin": ["John", "Doe"]}}

        self.assertEqual(
            str(builder.build(data.basic_enum_select, f_)),
            str(data.basic_enum_select.where(data.test_table.c.name.notin_(["John", "Doe"]))),
        )

    def test_advanced_selects(self):
        import src.siphon as ds
        from src.siphon.core import _exc as core_exc

        # TODO:
        # test select with multiple tables
        # test select with directly referencing column which might not be in the select
        # test labeled selects

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
        import src.siphon as ds
        from src.siphon.core import _exc as core_exc

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
        import src.siphon as ds
        from src.siphon.core import _exc as core_exc

        # TODO
        # test junctions above column names - joining multiple columns as filtering
        # test junctions below column names - joining multiple conditions on single column

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

    # NOTE: special input types such as datetime, date, time, etc. are supported in string format
    # and handled by SQLAlchemy, so no need to test them here


if __name__ == "__main__":
    unittest.main()
