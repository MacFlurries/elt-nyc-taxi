import os
import duckdb
from google.cloud import bigquery

PROJECT = os.environ["GCP_PROJECT_ID"]

con = duckdb.connect("warehouse/taxi.duckdb", read_only=True)
n_duck = con.sql("select count(*) from clean.yellow_trips").fetchall()[0][0]
con.close()

t = bigquery.Client(project=PROJECT).get_table(f"{PROJECT}.Taxi.clean_yellow_trips")
print("duckdb clean :", n_duck)
print("bigquery     :", t.num_rows)
print("sama         :", n_duck == t.num_rows)
for s in t.schema:
    if "datetime" in s.name or s.name in ("trip_distance", "passenger_count"):
        print(s.name, s.field_type)