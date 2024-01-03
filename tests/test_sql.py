import unittest
import sys
import data
sys.path.append(".")


class SQLTest(unittest.TestCase):

    def test_select_filtering(self):
        import src.siphon as ds

        # Test filtering - format

        # 2. keyword with invalid value
        with self.assertRaises(ds.sql.InvalidValueError):
            ds.build({'limit': {'eq': 1}}, ds.sql.SQL, data.tt_select)

        # 3. keyword order_by with invalid value
        with self.assertRaises(ds.sql.InvalidOperatorError):
            ds.build({'order_by': {'eq': 1}}, ds.sql.SQL, data.tt_select)

        # 4. keyword order_by with invalid value
        with self.assertRaises(ds.sql.FilterFormatError):
            ds.build({'order_by': 'name'}, ds.sql.SQL, data.tt_select)

        # 5. non-keyword with invalid value
        with self.assertRaises(ds.sql.FilterFormatError):
            ds.build({'name': 'John'}, ds.sql.SQL, data.tt_select)

        # 6. non-keyword with invalid operator
        with self.assertRaises(ds.sql.InvalidOperatorError):
            ds.build({'name': {'eq': 'John', 'invalid': 'invalid'}},
                     ds.sql.SQL, data.tt_select)

        # Test filtering - columns
        # 1. column not in select

        with self.assertRaises(ds.sql.FilterColumnError):
            ds.build({'build': {'eq': 'John'}}, ds.sql.SQL, data.st_select)

        # Test filtering - correct
        # 1. No filter
        self.assertEqual(
            str(ds.build({}, ds.sql.SQL, data.tt_select)), str(data.tt_select))

        # 2. Simple filter
        self.assertEqual(
            str(ds.build({'name': {'eq': 'John'}},
                ds.sql.SQL, data.tt_select)),
            str(data.tt_select.where(data.test_table.c.name == 'John')))

        # 3. Multiple filters
        self.assertEqual(
            str(ds.build({'name': {'eq': 'John'}, 'age': {'eq': 20}},
                         ds.sql.SQL, data.tt_select)),
            str(data.tt_select.where(
                (data.test_table.c.name == 'John') &
                (data.test_table.c.age == 20))))

        # 4. keyword limit
        self.assertEqual(
            str(ds.build({'limit': 3}, ds.sql.SQL, data.tt_select)),
            str(data.tt_select.limit(3)))

        # 5. keyword offset
        self.assertEqual(
            str(ds.build({'offset': 3}, ds.sql.SQL, data.tt_select)),
            str(data.tt_select.offset(3)))

        # 6. keyword order_by
        self.assertEqual(
            str(ds.build({'order_by': {'desc': 'name'}},
                         ds.sql.SQL, data.tt_select)),
            str(data.tt_select.order_by(data.test_table.c.name.desc())))

        # Test every operator
        # 1. eq

        self.assertEqual(
            str(ds.build({'name': {'eq': 'John'}},
                ds.sql.SQL, data.tt_select)),
            str(data.tt_select.where(data.test_table.c.name == 'John')))

        # 2. ne
        self.assertEqual(
            str(ds.build({'name': {'ne': 'John'}},
                ds.sql.SQL, data.tt_select)),
            str(data.tt_select.where(data.test_table.c.name != 'John')))

        # 3. gt
        self.assertEqual(
            str(ds.build({'age': {'gt': 20}}, ds.sql.SQL, data.tt_select)),
            str(data.tt_select.where(data.test_table.c.age > 20)))

        # 4. ge
        self.assertEqual(
            str(ds.build({'age': {'ge': 20}}, ds.sql.SQL, data.tt_select)),
            str(data.tt_select.where(data.test_table.c.age >= 20)))

        # 5. lt
        self.assertEqual(
            str(ds.build({'age': {'lt': 20}}, ds.sql.SQL, data.tt_select)),
            str(data.tt_select.where(data.test_table.c.age < 20)))

        # 6. le
        self.assertEqual(
            str(ds.build({'age': {'le': 20}}, ds.sql.SQL, data.tt_select)),
            str(data.tt_select.where(data.test_table.c.age <= 20)))

        # 7. in
        self.assertEqual(
            str(ds.build({'age': {'in_': [20, 21]}},
                ds.sql.SQL, data.tt_select)),
            str(data.tt_select.where(data.test_table.c.age.in_([20, 21]))))

        # 8. nin
        self.assertEqual(
            str(ds.build({'age': {'nin': [20, 21]}},
                ds.sql.SQL, data.tt_select)),
            str(data.tt_select.where(~data.test_table.c.age.in_([20, 21]))))

    def test_advanced_select(self):
        import src.siphon as ds

        # test combined tables
        self.assertEqual(
            str(ds.build({'name': {'eq': 'John'}, 'value': {'in_': [1, 2]}},
                         ds.sql.SQL, data.st_tt_select)),
            str(data.st_tt_select.where(
                (data.test_table.c.name == 'John') &
                (data.secondary_test.c.value.in_([1, 2])))))

        # test base table select
        self.assertEqual(
            str(ds.build({'name': {'eq': 'John'}},
                         ds.sql.SQL, data.base_select)),
            str(data.base_select.where(data.test_table.c.name == 'John')))

    def test_invalid_inputs(self):
        import src.siphon as ds

        # test invalid inputs
        # parsed dict with invalid operators
        with self.assertRaises(ds.base.SiphonError):
            ds.build({'name': {'invalid': 'John'}}, ds.sql.SQL, data.tt_select)

        # parsed dict which is not nested
        with self.assertRaises(ds.base.SiphonError):
            ds.build({'name': 'John'}, ds.sql.SQL, data.tt_select)

        # mistyped input
        with self.assertRaises(ds.base.SiphonError):
            ds.build({'name[eq': 'John'}, ds.sql.SQL, data.tt_select)


if __name__ == "__main__":
    unittest.main()
