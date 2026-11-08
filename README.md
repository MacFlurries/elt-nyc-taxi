# NYC Taxi ELT Pipeline

An ELT pipeline for NYC TLC Yellow Taxi trip data (Parquet).
It downloads data monthly, cleans it in DuckDB, builds a star schema with dbt,
and shows the result in a Metabase dashboard.
The same dbt models also run on BigQuery sandbox.

This is my first time using these tools. I was used to the native approach:
pulling data out of website HTML. Learning Data Engineering with Airflow, dbt,
and DuckDB felt like a breath of fresh air, and trying new tools was fun.

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

## What I learned

**Pipelines should be safe to re-run.**
I designed each layer so that running it again gives the same result: skip a
file that already exists, or delete one month and insert it again. Then I
checked it with evidence (file modified times did not change after a re-run).
"It should be idempotent" is not the same as "I showed it is idempotent".

**ELT with separate layers.**
Keeping `raw` (data as is) apart from `clean` (rules applied) means I can fix a
rule and rebuild without downloading again. I looked at the data first and
counted the problems before writing any cleaning rule.

**dbt makes SQL testable.**
Staging, marts, and a star schema gave the SQL a clear structure. Data tests
(`unique`, `not_null`, `relationships`, and custom SQL tests) check the data
every time the pipeline runs.

**SQL dialects are different.**
The same dbt model needed small changes between DuckDB and BigQuery: hash
functions, date functions, and table names. I handled them with
`target.type` branches and kept the working DuckDB branch untouched. I also
hit a template bug (a leftover comma) that I only found by reading the
compiled SQL.

**Version compatibility matters.**
The Metabase DuckDB driver needs a matching DuckDB version, so I rebuilt the
database file in a separate environment with DuckDB 1.5.6.

**Free tiers have rules.**
BigQuery sandbox tables expire after 60 days and DML is not supported. I
designed the BigQuery variant to be rebuilt from files, and I did not enable
billing.

**Keep secrets and project IDs out of the code.**
I moved the GCP project ID into an environment variable, used login-based
credentials instead of a key file, and checked what Git would upload before the
first commit.

**Docker details.**
Containers only see the folders you mount. Airflow could not write to my laptop
until I added a volume for `data/`.

**Verify, do not assume.**
Many of my first attempts failed for small reasons: wrong shell, wrong
folder, a placeholder I forgot to replace. Reading the exact error message
and checking each result before moving on saved the most time.

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