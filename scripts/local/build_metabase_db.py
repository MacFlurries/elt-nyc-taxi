import os

import duckdb

os.makedirs("metabase_data", exist_ok=True)
dst = "metabase_data/marts.duckdb"
if os.path.exists(dst):
    os.remove(dst)

print("duckdb", duckdb.__version__)
con = duckdb.connect(dst)
for t in ["dim_zone", "dim_payment_type", "dim_date", "fct_trips"]:
    con.sql(
        f"CREATE TABLE {t} AS "
        f"SELECT * FROM read_parquet('warehouse/marts_parquet/{t}.parquet')"
    )
    n = con.sql(f"SELECT count(*) FROM {t}").fetchall()[0][0]
    print(t, n)
con.close()