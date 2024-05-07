import sqlalchemy as sa

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

tt_select = sa.select(
    test_table.c.id,
    test_table.c.name,
    test_table.c.age,
    test_table.c.is_active,
    test_table.c.created_at,
).select_from(test_table)

st_select = sa.select(
    secondary_test.c.id,
    secondary_test.c.primary_id,
    secondary_test.c.value,
).select_from(secondary_test)

st_tt_select = sa.select(
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

base_select = test_table.select()

timestamp_table_select = table_with_time_stamp.select()
