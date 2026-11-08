# Arsitektur D1: NYC Taxi ELT

```mermaid
flowchart LR
    TLC["NYC TLC<br/>Yellow Taxi Parquet"] -->|"DAG download_tlc_yellow<br/>Airflow, 1 bulan per run"| RAWF["data/raw<br/>file Parquet"]

    subgraph DUCK["Jalur lokal: DuckDB"]
        RAWF -->|"scripts/local/elt.py"| RAW["raw.yellow_trips"]
        RAW -->|"dedup ROW_NUMBER<br/>+ aturan kualitas"| CLEAN["clean.yellow_trips"]
        CLEAN -->|"dbt, target dev"| MARTS["analytics:<br/>stg_yellow_trips, dim_zone,<br/>dim_payment_type, dim_date, fct_trips"]
    end

    MARTS -->|"export Parquet<br/>+ scripts/local/build_metabase_db.py"| MBDB["metabase_data/marts.duckdb"]
    MBDB --> MB["Metabase<br/>dashboard NYC Taxi"]

    subgraph BQ["Jalur cloud: BigQuery sandbox"]
        CLEAN -->|"scripts/bigquery/export_clean.py<br/>+ load_bq.py"| BQC["Taxi.clean_yellow_trips"]
        BQC -->|"dbt, target bq"| BQM["analytics:<br/>stg + dim_* + fct_trips"]
    end
```