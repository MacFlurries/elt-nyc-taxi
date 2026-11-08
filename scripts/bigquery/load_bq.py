import os
import glob

from google.cloud import bigquery

PROJECT = os.environ["GCP_PROJECT_ID"]
TABLE = f"{PROJECT}.Taxi.clean_yellow_trips"

client = bigquery.Client(project=PROJECT)
files = sorted(glob.glob("warehouse/export/clean_yellow_*.parquet"))

for i, path in enumerate(files):
    cfg = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=(
            bigquery.WriteDisposition.WRITE_TRUNCATE
            if i == 0
            else bigquery.WriteDisposition.WRITE_APPEND
        ),
    )
    with open(path, "rb") as f:
        job = client.load_table_from_file(
            f, TABLE, location="asia-southeast1", job_config=cfg
        )
    job.result()
    print("OK", path, job.output_rows)

t = client.get_table(TABLE)
print("rows:", t.num_rows)
for s in t.schema:
    print(s.name, s.field_type)