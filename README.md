# NYC Taxi ELT Pipeline

## Background

Before this project, I mostly collected data by pulling it out of website HTML.
I also worked with APIs and with automation using libraries and tools
([ISI: tulis library atau alat yang benar-benar Anda pakai]).
Those were scripts I ran by hand, one job at a time.

This was my first time building a full pipeline with Airflow, dbt, and DuckDB.
The data here is not scraped and not from an API. The TLC publishes monthly
Parquet files at public URLs, and an Airflow job downloads them. The new part
for me was the structure around the data: scheduling, layers, tests, and proof
that a re-run is safe.

Architecture diagram: [docs/architecture.md](docs/architecture.md)

## What this project shows

- Monthly ingestion that is idempotent: running it again does not duplicate rows.
- A star schema: 1 fact table (`fct_trips`) and 3 dimensions (`dim_zone`, `dim_payment_type`, `dim_date`).
- 14 automated dbt data tests.
- The same dbt models on two engines: DuckDB (local) and BigQuery sandbox (cloud).
- One Metabase dashboard.
- Everything runs on free or local tools.

## Pipeline at a glance

| Layer | Where | What happens | Why a re-run is safe |
|---|---|---|---|
| Download | `dags/download_tlc_yellow.py` (Airflow) | One month of Parquet per run, saved to `data/raw` | Skips a file that already exists. Writes to a temp file first, then renames |
| Raw | DuckDB, schema `raw` | Loads the Parquet as is, plus a `file_month` column | Deletes that month, then inserts it again |
| Clean | DuckDB, schema `clean` | Removes duplicates and bad rows | Deletes that month, then inserts it again |
| Staging and marts | dbt | Renames columns, builds the star schema | dbt rebuilds the tables |
| Dashboard | Metabase | Reads a read-only copy of the marts | Read-only |

## Data quality

Cleaning rules (`scripts/local/elt.py`):
- Remove duplicate rows with `ROW_NUMBER()`. The key is vendor, pickup time, dropoff time, pickup zone, dropoff zone, and total amount.
- Remove trips with distance of 0 or less.
- Remove trips where dropoff is before pickup.
- Remove trips whose pickup date is outside the month of the file.

dbt tests (14 defined):
- `unique` and `not_null` on the key of every table.
- `relationships` from the fact table to the zone (pickup and dropoff), payment type, and date dimensions.
- Two custom tests: distance must be positive, and dropoff must not be before pickup.

## Results

Fill these in from your own run:

| Item | Result |
|---|---|
| Months loaded | [ISI HASIL SETELAH DIKERJAKAN] |
| Rows in raw and clean | [ISI HASIL SETELAH DIKERJAKAN] |
| Rows in `fct_trips` (DuckDB and BigQuery) | [ISI HASIL SETELAH DIKERJAKAN] |
| dbt tests passed (DuckDB) | [ISI HASIL SETELAH DIKERJAKAN] |
| dbt tests passed (BigQuery) | [ISI HASIL SETELAH DIKERJAKAN] |
| Idempotency check (re-run changes nothing) | [ISI HASIL SETELAH DIKERJAKAN] |

## Data and license

- Source: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
- The source page says TLC makes no representations about the accuracy of the data.
- **License and terms of use: not verified.** Check the source page before reusing the data.
- The data is not included in this repo. Download it yourself (see below).

## Tools and versions

These are the versions I used. Other versions may work, but I have not tested them.

| Tool | Version |
|---|---|
| Docker Compose | v5.0.2 |
| Airflow | 3.3.2 (official quick-start Compose file) |
| Python | 3.13.7 |
| DuckDB (Python) | 2.0.0 |
| DuckDB for Metabase file | 1.5.6 |
| dbt | 1.12.6 |
| dbt-duckdb adapter | 1.11.1 |
| dbt-bigquery adapter | 1.12.2 |
| Metabase image | `ghcr.io/motherduckdb/metabase-duckdb:0.63.17-duckdb1.5.6.0` |

## Repository layout

```
dags/                     Airflow DAG (download_tlc_yellow)
dbt_taxi/                 dbt project (models, tests, profiles.yml)
docs/architecture.md      Architecture diagram
scripts/local/            DuckDB scripts and Metabase export
scripts/bigquery/         BigQuery export, load, and check scripts
docker-compose.yaml       Airflow (official file plus one extra volume for data/)
docker-compose.metabase.yml   Metabase with the DuckDB driver
```

## How to run

Run every command from the repo root.

**Prerequisites:** Docker with Compose v2.14 or newer and at least 4 GB of memory for Docker (Airflow docs say 8 GB is ideal), Python, and Git Bash on Windows.

**0. Python environment**
```bash
python -m venv .venv
source .venv/Scripts/activate     # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

**1. Download data with Airflow**
```bash
docker compose up airflow-init
docker compose up -d
```
Open http://localhost:8080 (default local account: `airflow` / `airflow`, for your own machine only).
Turn on the DAG `download_tlc_yellow`. It downloads Jan to Mar 2025 into `data/raw`.

**2. Raw and clean (DuckDB)**
```bash
python scripts/local/elt.py
```

**3. Zone lookup table** (not included in the repo)
```bash
curl -L -o dbt_taxi/seeds/taxi_zone_lookup.csv "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
```

**4. dbt on DuckDB**
```bash
cd dbt_taxi
dbt seed --profiles-dir .
dbt run  --profiles-dir .
dbt test --profiles-dir .
cd ..
```

**5. BigQuery variant** (optional)

Create a BigQuery sandbox project and a dataset named `Taxi`. The scripts use location `asia-southeast1`. Change it in `scripts/bigquery/load_bq.py` and `dbt_taxi/profiles.yml` if yours differs.
```bash
gcloud auth application-default login
export GCP_PROJECT_ID="your-project-id"
python scripts/bigquery/export_clean.py
python scripts/bigquery/load_bq.py
cd dbt_taxi
dbt seed --target bq --profiles-dir .
dbt run  --target bq --profiles-dir .
dbt test --target bq --profiles-dir .
cd ..
```

**6. Metabase dashboard**

The DuckDB version inside the Metabase driver must match the version that wrote the file. So the last step uses a separate environment with DuckDB 1.5.6.
```bash
python scripts/local/export_marts.py
python scripts/local/export_marts_parquet.py

python -m venv .venv-metabase
source .venv-metabase/Scripts/activate
pip install -r requirements-metabase.txt
python scripts/local/build_metabase_db.py
deactivate

docker compose -f docker-compose.metabase.yml up -d
```
Open http://localhost:3000. Add a DuckDB database, file path `/data/marts.duckdb`, read-only.

## Dashboard

Cards (edit this list to match what you built):
- Trips per day (area chart)
- Trips per payment type (bar chart)
- Trips per borough and month (pivot table, built with the query builder)

No map: `dim_zone` has no coordinates. Metabase pivot tables only work with questions built in the query builder, not SQL.

## Known limitations

- BigQuery sandbox tables expire after 60 days, and DML is not supported (per Google docs at the time of writing). So the BigQuery variant is always rebuilt from Parquet files.
- BigQuery dataset names are case-sensitive (`Taxi`).
- `trip_id` is a hash of key columns because the data has no trip ID. The hash function differs between DuckDB and BigQuery, so the same trip can get a different `trip_id` on each engine.
- Only the download step runs in Airflow. The other steps are manual scripts.
- The Metabase setup is not saved permanently. If the container is deleted, you must set up again.

## What I learned: the process, step by step

This is the order I worked in. I now see it as a general process for a data pipeline.

1. **Check the source first.** Read the data dictionary, find the real file URLs, and check the license. (License here: not verified.)
2. **Ingest so that a re-run is safe.** One month per run, skip files that exist, write to a temp file then rename. Then prove it: re-run and check that the files did not change.
3. **Profile before you clean.** Count the problems (duplicates, distance of 0 or less, dropoff before pickup, pickup outside the month) before writing any rule.
4. **Keep layers apart.** `raw` keeps the data as is. `clean` applies the rules. If a rule is wrong, rebuild `clean` from `raw` without downloading again.
5. **Model for questions.** Staging renames columns. Marts build the star schema: 1 fact and 3 dimensions. The data has no trip ID, so I built a key from a hash of columns and checked that it is unique.
6. **Test the data automatically.** Keys (`unique`, `not_null`), links between tables (`relationships`), and business rules (custom SQL tests). [ISI HASIL SETELAH DIKERJAKAN] tests passed.
7. **Run it on a second engine.** The same dbt models ran on BigQuery. Dialects differ (hash and date functions, table names), so I used `target.type` branches. I compared row counts across the two engines.
8. **Serve the result.** A Metabase dashboard reads a read-only copy of the marts. Version compatibility (the DuckDB driver) was a real constraint.
9. **Make it reproducible and honest.** Pinned versions in `requirements.txt`, run steps in the README, an architecture diagram, and a list of limitations.
10. **Protect and clean up.** No secrets or project IDs in the code, a `.gitignore` for data and local files, a check of what Git will upload before the first commit, and removal of local files that can be rebuilt.

The common thread: do not trust a result until you have checked it with evidence.

## Adapting this project

You can change these parts without changing what the project is about:
- **Months:** change `start_date` and `end_date` in `dags/download_tlc_yellow.py`. The other scripts read whatever files are in `data/raw`, and `dim_date` follows the data.
- **GCP project:** set `GCP_PROJECT_ID`. No code change needed.
- **BigQuery location:** change it in the two places listed in step 5.
- **Dashboard cards:** write your own queries on `fct_trips` and the dimensions.

If you change the cleaning rules or the star schema, update the Data quality section and the tests too.

## Rebuild everything

Delete `data/`, `warehouse/`, and `metabase_data/`, then repeat steps 1 to 6.
All of them can be rebuilt from the code.
