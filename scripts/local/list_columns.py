import duckdb

con = duckdb.connect("warehouse/taxi.duckdb", read_only=True)

tables = con.sql("""
    select table_schema, table_name, table_type
    from information_schema.tables
    where table_schema not in ('information_schema', 'pg_catalog')
    order by 1, 2
""").fetchall()

for schema, name, kind in tables:
    cols = con.sql(f"""
        select column_name, data_type
        from information_schema.columns
        where table_schema = '{schema}' and table_name = '{name}'
        order by ordinal_position
    """).fetchall()
    print(f"\n== {schema}.{name} ({kind}, {len(cols)} kolom)")
    for i, (col, dtype) in enumerate(cols, 1):
        print(f"{i:>2}. {col}  {dtype}")

con.close()