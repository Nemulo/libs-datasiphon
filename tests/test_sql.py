import unittest
import sys
import data
from pydantic import BaseModel
sys.path.append(".")


class SQLTest(unittest.TestCase):

    def test_select_filtering(self):
        import src.siphon as ds

        # Test filtering - format
        # 1. not a select
        with self.assertRaises(TypeError):
            ds.build({'name': {'eq': 'John'}}, ds.sql.SQL, data.test_table)

        # 2. keyword with invalid value
        with self.assertRaises(ds.sql.FilterFormatError):
            ds.build({'limit': {'eq': 1}}, ds.sql.SQL, data.tt_select)

        # 3. keyword order_by with invalid value
        with self.assertRaises(ds.sql.FilterFormatError):
            ds.build({'order_by': {'eq': 1}}, ds.sql.SQL, data.tt_select)

        # 4. keyword order_by with invalid value
        with self.assertRaises(ds.sql.InvalidValueError):
            ds.build({'order_by': 'name'}, ds.sql.SQL, data.tt_select)

        # 5. non-keyword with invalid value
        with self.assertRaises(ds.sql.FilterFormatError):
            ds.build({'name': 'John'}, ds.sql.SQL, data.tt_select)

        # 6. non-keyword with invalid operator - now ignored invalid operations TODO
        self.assertEqual(
            str(ds.build({'name': {'eq': 'John', 'invalid': 'invalid'}},
                         ds.sql.SQL, data.tt_select)),
            str(data.tt_select.where(data.test_table.c.name == 'John')))

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
            str(ds.build({'order_by': 'name.desc'},
                         ds.sql.SQL, data.tt_select)),
            str(data.tt_select.order_by(data.test_table.c.name.desc())))

        self.assertEqual(
            str(ds.build({'order_by': 'name.asc'},
                         ds.sql.SQL, data.tt_select)),
            str(data.tt_select.order_by(data.test_table.c.name.asc())))

        self.assertEqual(
            str(ds.build({'order_by': '+name'},
                         ds.sql.SQL, data.tt_select)),
            str(data.tt_select.order_by(data.test_table.c.name.asc())))

        self.assertEqual(
            str(ds.build({'order_by': '-name'},
                         ds.sql.SQL, data.tt_select)),
            str(data.tt_select.order_by(data.test_table.c.name.desc())))

        self.assertEqual(
            str(ds.build({'order_by': 'asc(name)'},
                         ds.sql.SQL, data.tt_select)),
            str(data.tt_select.order_by(data.test_table.c.name.asc())))

        self.assertEqual(
            str(ds.build({'order_by': 'desc(name)'},
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

        # test filter not correct type
        with self.assertRaises(ds.sql.InvalidValueError):
            ds.build({'name': {'eq': 1}}, ds.sql.SQL, data.tt_select)

        # test multiple order by's
        with self.assertRaises(ds.sql.FilterFormatError):
            ds.build({'order_by': {'desc': 'name', 'asc': 'age'}},
                     ds.sql.SQL, data.tt_select)

    def test_advanced_select(self):
        import src.siphon as ds

        # test combined tables - should raise error since value is of type string
        # NOTE functionality updated v 0.1.0
        with self.assertRaises(ds.sql.InvalidValueError):
            ds.build({'name': {'eq': 'John'}, 'value': {'in_': [1, 2]}},
                     ds.sql.SQL, data.st_tt_select)

        # combined tables correct select
        self.assertEqual(
            str(ds.build({'name': {'eq': 'John'}, 'value': {'in_': ['abc', 'def']}},
                         ds.sql.SQL, data.st_tt_select)),
            str(data.st_tt_select.where(
                data.test_table.c.name == 'John',
                data.secondary_test.c.value.in_(['abc', 'def']))
                )
        ),
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

    def test_restricted_inputs(self):
        import src.siphon as ds

        # test non restricted select with single order by
        self.assertEqual(
            str(ds.sql.SQL.build(data.tt_select, {'order_by': 'name.desc'})),
            str(data.tt_select.order_by(data.test_table.c.name.desc()))
        )

        # restrictions on filters
        class BaseUserRestriction(BaseModel):
            name: list[str] = ['eq', 'ne']

        restriction = BaseUserRestriction()

        # test restricted select with single order by
        with self.assertRaises(ds.sql.FilterFormatError):
            ds.sql.SQL.build(data.tt_select, {'order_by': 'name.desc'}, filter_model=restriction)

        # test restricted select
        with self.assertRaises(ds.sql.InvalidOperatorError):
            ds.sql.SQL.build(data.tt_select, {'name': {'in_': 'John'}}, filter_model=restriction)

        class AdvancedUserRestriction(BaseModel):
            name: list[str] = ['eq', 'ne']
            age: list[str] = ['eq', 'ne', 'in_']
            value: list[str] = ['in_']
            order_by: list[str] = ['name', 'age']
            limit: bool = True

        restriction = AdvancedUserRestriction()

        # test restricted select with single order by
        self.assertEqual(
            str(ds.sql.SQL.build(data.st_tt_select, {'order_by': 'name.desc'}, filter_model=restriction)),
            str(data.st_tt_select.order_by(data.test_table.c.name.desc()))
        )

        # test restricted select
        self.assertEqual(
            str(ds.sql.SQL.build(data.st_tt_select, {'name': {'eq': 'John'}}, filter_model=restriction)),
            str(data.st_tt_select.where(data.test_table.c.name == 'John'))
        )

        # test invalid order by column
        with self.assertRaises(ds.sql.InvalidRestrictionModel):
            ds.sql.SQL.build(data.tt_select, {'order_by': 'name.desc'}, filter_model=restriction)

        # invalid restriction model
        class InvalidRestriction(BaseModel):
            name: str = 'eq'

        restriction = InvalidRestriction()

        with self.assertRaises(ds.sql.InvalidRestrictionModel):
            ds.sql.SQL.build(data.tt_select, {'name': {'eq': 'John'}}, filter_model=restriction)

        class InvalidRestrictionKeyword(BaseModel):
            limit: int = 10

        restriction = InvalidRestrictionKeyword()

        with self.assertRaises(ds.sql.InvalidRestrictionModel):
            ds.sql.SQL.build(data.tt_select, {'limit': 10}, filter_model=restriction)

        class InvalidRestrictionOperators(BaseModel):
            name: list[str] = ['eq', 'ne', 'invalid']

        restriction = InvalidRestrictionOperators()

        with self.assertRaises(ds.sql.InvalidOperatorError):
            ds.sql.SQL.build(data.tt_select, {'name': {'eq': 'John'}}, filter_model=restriction)

        class InvalidOrderByColumns(BaseModel):
            order_by: list[str] = ['name', 'invalid']

        restriction = InvalidOrderByColumns()

        with self.assertRaises(ds.sql.InvalidRestrictionModel):
            ds.sql.SQL.build(data.tt_select, {'order_by': 'name.desc'}, filter_model=restriction)

        class NonExistentCol(BaseModel):
            invalid: list[str] = ['eq', 'ne']

        restriction = NonExistentCol()

        with self.assertRaises(ds.sql.InvalidRestrictionModel):
            ds.sql.SQL.build(data.tt_select, {'invalid': {'eq': 'John'}}, filter_model=restriction)

    def test_multiple_order_by(self):
        import src.siphon as ds

        # test multiple order by's
        self.assertEqual(
            str(ds.build({'order_by': ['name.desc', 'age.asc']},
                         ds.sql.SQL, data.tt_select)),
            str(data.tt_select.order_by(data.test_table.c.name.desc(), data.test_table.c.age.asc())))

        # test multiple order by's with invalid column
        with self.assertRaises(ds.sql.FilterColumnError):
            ds.build({'order_by': ['name.desc', 'invalid.asc']},
                     ds.sql.SQL, data.tt_select)

        # test multiple order by's with invalid operator
        with self.assertRaises(ds.sql.InvalidValueError):
            ds.build({'order_by': ['name.desc', 'age.invalid']},
                     ds.sql.SQL, data.tt_select)

    def test_ignore_extra_param(self):
        import src.siphon as ds

        class AdvancedUserRestriction(BaseModel):
            name: list[str] = ['eq', 'ne']
            age: list[str] = ['eq', 'ne', 'in_']
            order_by: list[str] = ['name', 'age']
            limit: bool = True

        restriction = AdvancedUserRestriction()

        # test restricted select while not ignoring extra params
        with self.assertRaises(ds.sql.FilterFormatError):
            ds.sql.SQL.build(
                data.st_tt_select, {'name': {'eq': 'John'},
                                    'extra': {'eq': 'extra'}},
                filter_model=restriction)

        # test restricted select while ignoring extra params
            self.assertEqual(
                str(ds.sql.SQL.build(
                    data.st_tt_select, {'name': {'eq': 'John'},
                                        'extra': {'eq': 'extra'}},
                    filter_model=restriction, ignore_extra_fields=True)),
                str(data.st_tt_select.where(data.test_table.c.name == 'John'))
            )

        # test restricted select while not ignoring extra params although its valid column
        with self.assertRaises(ds.sql.FilterFormatError):
            ds.sql.SQL.build(
                data.st_tt_select, {'name': {'eq': 'John'},
                                    'value': {'eq': 'extra'}},
                filter_model=restriction)

        # test restricted select while ignoring extra params although its valid column
        self.assertEqual(
            str(ds.sql.SQL.build(
                data.st_tt_select, {'name': {'eq': 'John'},
                                    'value': {'eq': 'extra'}},
                filter_model=restriction, ignore_extra_fields=True)),
            str(data.st_tt_select.where(data.test_table.c.name == 'John'))
        )

        # test restricted select while ignoring extra params resulting in empty filter
        self.assertEqual(
            str(ds.sql.SQL.build(
                data.st_tt_select, {'value': {'eq': 'extra'}},
                filter_model=restriction, ignore_extra_fields=True)),
            str(data.st_tt_select)
        )

        # test restricted select while ignoring extra params for potentionally bad format of filter
        with self.assertRaises(ds.base.FilterFormatError):
            str(ds.sql.SQL.build(
                data.st_tt_select, {'value': 'ok'},
                filter_model=restriction, ignore_extra_fields=True))

    def test_strict_filtering(self):
        import src.siphon as ds

        # test strict (by default)
        self.assertEqual(
            str(ds.sql.SQL.build(data.tt_select, {'name': {'eq': 'John'}})),
            str(data.tt_select.where(data.test_table.c.name == 'John'))
        )

        with self.assertRaises(ds.sql.FilterFormatError):
            ds.sql.SQL.build(data.tt_select, {'name': "John"})

        # test not strict
        self.assertEqual(
            str(ds.sql.SQL.build(data.tt_select, {'name': "John"}, strict=False)),
            str(data.tt_select)
        )

        self.assertEqual(
            str(ds.sql.SQL.build(data.tt_select, {'name': {'eq': 'John'}, "age": 20}, strict=False)),
            str(data.tt_select.where(data.test_table.c.name == 'John'))
        )


if __name__ == "__main__":
    unittest.main()
