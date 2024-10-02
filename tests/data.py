import sqlalchemy as sa
import enum

test_table = sa.Table(
    "tt",
    sa.MetaData(),
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("name", sa.String(50), nullable=False),
    sa.Column("age", sa.Integer, nullable=False),
    sa.Column("is_active", sa.Boolean, nullable=False),
    sa.Column("created_at", sa.DateTime, nullable=False),
)

secondary_test = sa.Table(
    "st",
    sa.MetaData(),
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("primary_id", sa.Integer, sa.ForeignKey("tt.id"), nullable=False),
    sa.Column("value", sa.String(50), nullable=False),
)

table_with_time_stamp = sa.Table(
    "tts",
    sa.MetaData(),
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("name", sa.String(50), nullable=False),
    sa.Column("created_at", sa.DateTime, nullable=False),
)


class TestEnum(enum.Enum):
    A = 1
    B = 2
    C = 3


nullables_generic_types_table = sa.Table(
    "ngt",
    sa.MetaData(),
    sa.Column("id", sa.BigInteger, primary_key=True),
    sa.Column("bool_type", sa.Boolean, nullable=True),
    sa.Column("date_type", sa.Date, nullable=True),
    sa.Column("datetime_type", sa.DateTime, nullable=True),
    sa.Column("enum_type", sa.Enum(TestEnum), nullable=True),
    sa.Column("double_type", sa.Double, nullable=True),
    sa.Column("float_type", sa.Float, nullable=True),
    sa.Column("int_type", sa.Integer, nullable=True),
    sa.Column("interval_type", sa.Interval, nullable=True),
    sa.Column("large_binary_type", sa.LargeBinary, nullable=True),
    # matchtype not supported
    sa.Column("pickletype_type", sa.PickleType, nullable=True),
    # schema type not supported
    sa.Column("small_integer_type", sa.SmallInteger, nullable=True),
    sa.Column("string_type", sa.String, nullable=True),
    sa.Column("text_type", sa.Text, nullable=True),
    sa.Column("time_type", sa.Time, nullable=True),
    sa.Column("unicode_type", sa.Unicode, nullable=True),
    sa.Column("unicode_text_type", sa.UnicodeText, nullable=True),
    sa.Column("uuid_type", sa.UUID, nullable=True),
)

nullables_standard_uppercase_table = sa.Table(
    "sut",
    sa.MetaData(),
    sa.Column("id", sa.BIGINT, primary_key=True),
    sa.Column("array_type", sa.ARRAY(sa.Integer), nullable=True),
    sa.Column("binary_type", sa.BINARY, nullable=True),
    sa.Column("blob_type", sa.BLOB, nullable=True),
    sa.Column("boolean_type", sa.BOOLEAN, nullable=True),
    sa.Column("char_type", sa.CHAR, nullable=True),
    sa.Column("clob_type", sa.CLOB, nullable=True),
    sa.Column("date_type", sa.DATE, nullable=True),
    sa.Column("datetime_type", sa.DATETIME, nullable=True),
    sa.Column("decimal_type", sa.DECIMAL, nullable=True),
    sa.Column("double_type", sa.DOUBLE, nullable=True),
    sa.Column("double_precision_type", sa.DOUBLE_PRECISION, nullable=True),
    sa.Column("float_type", sa.FLOAT, nullable=True),
    sa.Column("int_type", sa.INT, nullable=True),
    sa.Column("json_type", sa.JSON, nullable=True),
    sa.Column("nchar_type", sa.NCHAR, nullable=True),
    sa.Column("nvarchar_type", sa.NVARCHAR, nullable=True),
    sa.Column("numeric_type", sa.NUMERIC, nullable=True),
    sa.Column("real_type", sa.REAL, nullable=True),
    sa.Column("small_integer_type", sa.SMALLINT, nullable=True),
    sa.Column("text_type", sa.TEXT, nullable=True),
    sa.Column("time_type", sa.TIME, nullable=True),
    sa.Column("timestamp_type", sa.TIMESTAMP, nullable=True),
    sa.Column("uuid_type", sa.UUID, nullable=True),
    sa.Column("varbinary_type", sa.VARBINARY, nullable=True),
    sa.Column("varchar_type", sa.VARCHAR, nullable=True),
)


partial_select = sa.select(
    test_table.c.name,
    test_table.c.age,
).select_from(test_table)

partial_combined_select = sa.select(
    test_table.c.name,
    test_table.c.age,
    secondary_test.c.value,
).select_from(
    test_table.join(
        secondary_test,
        test_table.c.id == secondary_test.c.primary_id,
    )
)

basic_enum_select = sa.select(
    test_table.c.id,
    test_table.c.name,
    test_table.c.age,
    test_table.c.is_active,
    test_table.c.created_at,
).select_from(test_table)

secondary_table_select = sa.select(
    secondary_test.c.id,
    secondary_test.c.primary_id,
    secondary_test.c.value,
).select_from(secondary_test)

combined_enum_select = sa.select(
    test_table.c.id,
    test_table.c.name,
    test_table.c.age,
    test_table.c.is_active,
    test_table.c.created_at,
    secondary_test.c.id,
    secondary_test.c.primary_id,
    secondary_test.c.value,
).select_from(
    test_table.outerjoin(
        secondary_test,
        test_table.c.id == secondary_test.c.primary_id,
    )
)

labeled_select = sa.select(
    test_table.c.id.label("ID"),
    test_table.c.name.label("tt_name"),
    test_table.c.age.label("tt_age"),
).select_from(test_table)

labeled_combined_select = sa.select(
    test_table.c.id.label("ID"),
    test_table.c.name.label("tt_name"),
    test_table.c.age.label("tt_age"),
    secondary_test.c.id.label("ST_ID"),
    secondary_test.c.primary_id.label("ST_PRIMARY_ID"),
    secondary_test.c.value.label("ST_VALUE"),
).select_from(
    test_table.join(
        secondary_test,
        test_table.c.id == secondary_test.c.primary_id,
    )
)

base_select = test_table.select()

timestamp_table_select = table_with_time_stamp.select()
