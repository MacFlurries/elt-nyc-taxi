import glob
import os
import re

import duckdb

os.makedirs("warehouse", exist_ok=True)
con = duckdb.connect("warehouse/taxi.duckdb")
con.sql("CREATE SCHEMA IF NOT EXISTS raw")
con.sql("CREATE SCHEMA IF NOT EXISTS clean")

files = sorted(glob.glob("data/raw/yellow_tripdata_*.parquet"))

con.sql(f"""
CREATE TABLE IF NOT EXISTS raw.yellow_trips AS
SELECT *, ''::VARCHAR AS file_month FROM read_parquet('{files[0]}') WHERE false
""")
con.sql("CREATE TABLE IF NOT EXISTS clean.yellow_trips AS SELECT * FROM raw.yellow_trips WHERE false")


def load_month(path):
    month = re.search(r"(\d{4}-\d{2})", path).group(1)

    # RAW: hapus bulan ini, isi ulang -> jalan ulang tidak menggandakan baris
    con.sql(f"DELETE FROM raw.yellow_trips WHERE file_month = '{month}'")
    con.sql(f"""
        INSERT INTO raw.yellow_trips BY NAME
        SELECT *, '{month}' AS file_month FROM read_parquet('{path}')
    """)

    # CLEAN: dedup + aturan kualitas, juga per bulan
    con.sql(f"DELETE FROM clean.yellow_trips WHERE file_month = '{month}'")
    con.sql(f"""
        INSERT INTO clean.yellow_trips BY NAME
        SELECT * EXCLUDE (rn) FROM (
            SELECT *, ROW_NUMBER() OVER (
                PARTITION BY VendorID, tpep_pickup_datetime, tpep_dropoff_datetime,
                             PULocationID, DOLocationID, total_amount
                ORDER BY file_month
            ) AS rn
            FROM raw.yellow_trips WHERE file_month = '{month}'
        )
        WHERE rn = 1
          AND trip_distance > 0
          AND tpep_dropoff_datetime >= tpep_pickup_datetime
          AND strftime(tpep_pickup_datetime, '%Y-%m') = file_month
    """)


for f in files:
    load_month(f)

print(con.sql("""
SELECT r.file_month, r.n AS raw_rows, coalesce(c.n, 0) AS clean_rows
FROM (SELECT file_month, count(*) n FROM raw.yellow_trips GROUP BY 1) r
LEFT JOIN (SELECT file_month, count(*) n FROM clean.yellow_trips GROUP BY 1) c USING (file_month)
ORDER BY 1
"""))
con.close()