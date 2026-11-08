import duckdb

con = duckdb.connect()
con.sql("""
CREATE VIEW raw AS
SELECT *, regexp_extract(filename, '(\\d{4}-\\d{2})', 1) AS file_month
FROM read_parquet('data/raw/*.parquet', filename=true, union_by_name=true)
""")

print(con.sql("""
SELECT
  count(*) AS total_rows,
  count(*) - (SELECT count(*) FROM (
      SELECT DISTINCT * EXCLUDE (filename, file_month) FROM raw)) AS exact_dupes,
  count(*) FILTER (WHERE trip_distance <= 0) AS dist_le_0,
  count(*) FILTER (WHERE tpep_dropoff_datetime < tpep_pickup_datetime) AS drop_before_pick,
  count(*) FILTER (WHERE tpep_pickup_datetime IS NULL
                      OR tpep_dropoff_datetime IS NULL) AS null_times,
  count(*) FILTER (WHERE strftime(tpep_pickup_datetime, '%Y-%m') <> file_month) AS pickup_outside_month
FROM raw
"""))