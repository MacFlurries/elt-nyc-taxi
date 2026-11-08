import os

import duckdb

os.makedirs("warehouse/export", exist_ok=True)
con = duckdb.connect("warehouse/taxi.duckdb", read_only=True)

months = [
    r[0]
    for r in con.sql(
        "select distinct file_month from clean.yellow_trips order by 1"
    ).fetchall()
]

for m in months:
    out = f"warehouse/export/clean_yellow_{m}.parquet"
    con.sql(
        f"COPY (SELECT * FROM clean.yellow_trips WHERE file_month = '{m}') "
        f"TO '{out}' (FORMAT parquet)"
    )
    print(m, os.path.getsize(out), "bytes")

con.close()