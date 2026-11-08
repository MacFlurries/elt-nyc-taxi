import duckdb

f = "data/raw/yellow_tripdata_2025-01.parquet"
con = duckdb.connect()
print(con.sql(f"DESCRIBE SELECT * FROM '{f}'"))
print(con.sql(f"SELECT count(*) AS n FROM '{f}'"))
print(con.sql(f"SELECT * FROM '{f}' LIMIT 3"))