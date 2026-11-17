import os

import duckdb

TABLES = ["dim_zone", "dim_payment_type", "dim_date", "fct_trips",
          "fct_fleet_hourly", "fct_zone_daytype"]

os.makedirs("metabase_data", exist_ok=True)
dst = "metabase_data/marts.duckdb"
for f in (dst, dst + ".wal"):
    if os.path.exists(f):
        os.remove(f)

print("duckdb", duckdb.__version__)
con = duckdb.connect(dst)
for t in TABLES:
    con.sql(
        f"CREATE TABLE {t} AS "
        f"SELECT * FROM read_parquet('warehouse/marts_parquet/{t}.parquet')"
    )
    n = con.sql(f"SELECT count(*) FROM {t}").fetchall()[0][0]
    print(t, n)
con.execute("CHECKPOINT")
con.close()

chk = duckdb.connect(dst, read_only=True)
names = sorted(r[0] for r in chk.sql(
    "select table_name from information_schema.tables where table_schema='main'"
).fetchall())
print("tabel terbaca ulang:", len(names), names)
chk.close()
print("wal masih ada:", os.path.exists(dst + ".wal"))
