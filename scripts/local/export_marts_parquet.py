import os

import duckdb

os.makedirs("warehouse/marts_parquet", exist_ok=True)
con = duckdb.connect("warehouse/marts.duckdb", read_only=True)

for t in ["dim_zone", "dim_payment_type", "dim_date", "fct_trips"]:
    out = f"warehouse/marts_parquet/{t}.parquet"
    con.sql(f"COPY {t} TO '{out}' (FORMAT parquet)")
    print(t, os.path.getsize(out), "bytes")

con.close()