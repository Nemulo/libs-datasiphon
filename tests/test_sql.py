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
            builder.build(data.tt_select, f_)

        # keyword with invalid values - offset not int-like
        f_ = {"offset": "john"}

        with self.assertRaises(core_exc.InvalidValueTypeError):
            builder.build(data.tt_select, f_)

        # keyword with invalid values - order incorrect format
        f_ = {"order_by": "john"}

        with self.assertRaises(core_exc.BadFormatError):
            builder.build(data.tt_select, f_)

        f_ = {"order_by": ["john", "doe"]}
        with self.assertRaises(core_exc.BadFormatError):
            builder.build(data.tt_select, f_)

        # bad filter format - column without operator
        f_ = {"name": "john"}
        with self.assertRaises(core_exc.InvalidFilteringStructureError):
            builder.build(data.tt_select, f_)

        # bad filter format - column with unknown operator
        f_ = {"name": {"unknown": "john"}}
        with self.assertRaises(core_exc.InvalidFilteringStructureError):
            builder.build(data.tt_select, f_)

        # operator without column
        f_ = {"eq": "john"}
        with self.assertRaises(core_exc.InvalidFilteringStructureError):
            builder.build(data.tt_select, f_)

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
            builder.build(data.tt_select, f_)

        # test with no filter
        f_ = {}
        self.assertEqual(
            str(builder.build(data.tt_select, f_)),
            str(data.tt_select),
        )

        # simple filter
        f_ = {"name": {"eq": "John"}}
        self.assertEqual(
            str(builder.build(data.tt_select, f_)),
            str(data.tt_select.where(data.test_table.c.name == "John")),
        )

        # multiple filters
        f_ = {"name": {"eq": "John"}, "age": {"gt": 20}}
        self.assertEqual(
            str(builder.build(data.tt_select, f_)),
            str(
                data.tt_select.where(
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
            str(builder.build(data.tt_select, f_)),
            str(data.tt_select.limit(10)),
        )

        # test offset
        f_ = {"offset": 10}
        self.assertEqual(
            str(builder.build(data.tt_select, f_)),
            str(data.tt_select.offset(10)),
        )

        # test order by - multiple formats available
        f_ = {"order_by": "+name"}
        self.assertEqual(
            str(builder.build(data.tt_select, f_)),
            str(data.tt_select.order_by(data.test_table.c.name.asc())),
        )

        f_ = {"order_by": "-name"}
        self.assertEqual(
            str(builder.build(data.tt_select, f_)),
            str(data.tt_select.order_by(data.test_table.c.name.desc())),
        )

        f_ = {"order_by": "asc(name)"}
        self.assertEqual(
            str(builder.build(data.tt_select, f_)),
            str(data.tt_select.order_by(data.test_table.c.name.asc())),
        )

        f_ = {"order_by": "desc(name)"}
        self.assertEqual(
            str(builder.build(data.tt_select, f_)),
            str(data.tt_select.order_by(data.test_table.c.name.desc())),
        )

        f_ = {"order_by": "name.asc"}
        self.assertEqual(
            str(builder.build(data.tt_select, f_)),
            str(data.tt_select.order_by(data.test_table.c.name.asc())),
        )

        f_ = {"order_by": "name.desc"}
        self.assertEqual(
            str(builder.build(data.tt_select, f_)),
            str(data.tt_select.order_by(data.test_table.c.name.desc())),
        )

        f_ = {"order_by": ["+name", "-age"]}
        self.assertEqual(
            str(builder.build(data.tt_select, f_)),
            str(data.tt_select.order_by(data.test_table.c.name.asc(), data.test_table.c.age.desc())),
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
            str(builder.build(data.tt_select, f_)),
            str(data.tt_select.where(data.test_table.c.name == "John")),
        )

        # test ne
        f_ = {"name": {"ne": "John"}}
        self.assertEqual(
            str(builder.build(data.tt_select, f_)),
            str(data.tt_select.where(data.test_table.c.name != "John")),
        )

        # test gt
        f_ = {"age": {"gt": 20}}
        self.assertEqual(
            str(builder.build(data.tt_select, f_)),
            str(data.tt_select.where(data.test_table.c.age > 20)),
        )

        # test ge
        f_ = {"age": {"ge": 20}}
        self.assertEqual(
            str(builder.build(data.tt_select, f_)),
            str(data.tt_select.where(data.test_table.c.age >= 20)),
        )

        # test lt
        f_ = {"age": {"lt": 20}}
        self.assertEqual(
            str(builder.build(data.tt_select, f_)),
            str(data.tt_select.where(data.test_table.c.age < 20)),
        )

        # test le
        f_ = {"age": {"le": 20}}
        self.assertEqual(
            str(builder.build(data.tt_select, f_)),
            str(data.tt_select.where(data.test_table.c.age <= 20)),
        )

        # test in_
        # if not list - should raise error
        with self.assertRaises(core.InvalidValueTypeError):
            f_ = {"name": {"in_": "John"}}
            builder.build(data.tt_select, f_)

        f_ = {"name": {"in_": ["John", "Doe"]}}

        self.assertEqual(
            str(builder.build(data.tt_select, f_)),
            str(data.tt_select.where(data.test_table.c.name.in_(["John", "Doe"]))),
        )

        # test not_in
        # if not list - should raise error
        with self.assertRaises(core.InvalidValueTypeError):
            f_ = {"name": {"nin": "John"}}
            builder.build(data.tt_select, f_)

        f_ = {"name": {"nin": ["John", "Doe"]}}

        self.assertEqual(
            str(builder.build(data.tt_select, f_)),
            str(data.tt_select.where(data.test_table.c.name.notin_(["John", "Doe"]))),
        )

    def test_advanced_selects(self):
        # TODO:
        # test select with multiple tables
        # test select with directly referencing column which might not be in the select
        ...

    def test_filter_restrictions(self):
        # TODO implement restrictions and test
        ...

    def test_junctions(self):
        # TODO
        # test junctions above column names - joining multiple columns as filtering
        # test junctions below column names - joining multiple conditions on single column
        ...

    def test_special_input_types(self):
        # TODO
        # test for special input types like datetime, date, time, etc.
        ...

    def test_pagination(self):
        # TODO implement pagination and test
        ...


if __name__ == "__main__":
    unittest.main()
