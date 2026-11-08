import os

import duckdb

SRC = "warehouse/taxi.duckdb"
DST = "warehouse/marts.duckdb"

if os.path.exists(DST):
    os.remove(DST)

con = duckdb.connect(DST)
con.sql(f"ATTACH '{SRC}' AS src (READ_ONLY)")
for t in ["dim_zone", "dim_payment_type", "dim_date", "fct_trips"]:
    con.sql(f"CREATE TABLE {t} AS SELECT * FROM src.analytics.{t}")
    n = con.sql(f"SELECT count(*) FROM {t}").fetchall()[0][0]
    print(t, n)
con.close()