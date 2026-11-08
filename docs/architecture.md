# Architecture: NYC Taxi ELT

Data flows from the NYC TLC public files to a Metabase dashboard.
The same dbt models run on two engines: DuckDB (local) and BigQuery sandbox (cloud).

## Pipeline flow

```mermaid
%%{init: {"theme":"base","themeVariables":{"fontFamily":"Inter, Segoe UI, sans-serif","fontSize":"16px","lineColor":"#64748b","textColor":"#1e293b","edgeLabelBackground":"#f8fafc"},"flowchart":{"curve":"step","nodeSpacing":40,"rankSpacing":50,"padding":12}}}%%
flowchart TB
    TLC(["🗽 <b>NYC TLC</b><br/>Yellow Taxi Parquet"]):::source
    ZONE(["🗺️ <b>TLC Zone Lookup</b><br/>taxi_zone_lookup.csv"]):::source
    RAWF[("📁 <b>data/raw</b><br/>file Parquet")]:::storage

    subgraph DUCK["🦆 Jalur Lokal · DuckDB"]
        RAW[("🥉 <b>raw</b><br/>yellow_trips")]:::raw
        CLEAN[("🥈 <b>clean</b><br/>yellow_trips")]:::clean
        MARTS["🥇 <b>analytics</b><br/>stg_yellow_trips<br/>dim_zone · dim_payment_type<br/>dim_date · fct_trips"]:::mart
    end

    MBDB[("🗄️ <b>marts.duckdb</b><br/>DuckDB 1.5.6")]:::storage
    MB(["📈 <b>Metabase</b><br/>Dashboard NYC Taxi"]):::bi

    subgraph BQ["☁️ Jalur Cloud · BigQuery"]
        BQC[("🥈 <b>clean</b><br/>Taxi.clean_yellow_trips")]:::clean
        BQM["🥇 <b>analytics</b><br/>stg + dim_* + fct_trips"]:::mart
    end

    %% ---- Alur (urutan edge dipakai oleh linkStyle di bawah) ----
    TLC  -->|"Airflow DAG · 1 bulan per run"| RAWF
    RAWF -->|"elt.py"| RAW
    RAW  -->|"dedup + aturan kualitas"| CLEAN
    CLEAN -->|"dbt · dev"| MARTS
    MARTS -->|"export_marts.py → Parquet → build_metabase_db.py"| MBDB
    MBDB --> MB
    CLEAN -.->|"export_clean.py + load_bq.py"| BQC
    BQC  -->|"dbt · bq"| BQM
    ZONE -.->|"curl + dbt seed"| MARTS
    ZONE -.->|"dbt seed · bq"| BQM

    classDef source  fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#075985
    classDef storage fill:#f1f5f9,stroke:#64748b,stroke-width:2px,color:#334155
    classDef raw     fill:#ffedd5,stroke:#ea580c,stroke-width:2px,color:#9a3412
    classDef clean   fill:#e2e8f0,stroke:#475569,stroke-width:2px,color:#1e293b
    classDef mart    fill:#fef9c3,stroke:#ca8a04,stroke-width:2px,color:#713f12
    classDef bi      fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#14532d

    style DUCK fill:#fffbeb,stroke:#f59e0b,stroke-width:2px,stroke-dasharray:5 5,color:#92400e
    style BQ   fill:#eff6ff,stroke:#3b82f6,stroke-width:2px,stroke-dasharray:5 5,color:#1e3a8a

    linkStyle 3 stroke:#f59e0b,stroke-width:3px
    linkStyle 4,5 stroke:#16a34a,stroke-width:3px
    linkStyle 6 stroke:#3b82f6,stroke-width:3px,stroke-dasharray:6 4
    linkStyle 7 stroke:#3b82f6,stroke-width:3px
    linkStyle 8 stroke:#f59e0b,stroke-width:2px
    linkStyle 9 stroke:#3b82f6,stroke-width:2px
```

## Star schema

```mermaid
erDiagram
    dim_date ||--o{ fct_trips : "pickup_date_id"
    dim_zone ||--o{ fct_trips : "pickup_zone_id"
    dim_zone ||--o{ fct_trips : "dropoff_zone_id"
    dim_payment_type ||--o{ fct_trips : "payment_type_id"

    fct_trips {
        string trip_id PK
        int pickup_date_id FK
        int pickup_zone_id FK
        int dropoff_zone_id FK
        int payment_type_id FK
        int vendor_id
        int ratecode_id
        timestamp pickup_at
        timestamp dropoff_at
        int passenger_count
        double trip_distance
        double fare_amount
        double tip_amount
        double tolls_amount
        double congestion_surcharge
        double airport_fee
        double cbd_congestion_fee
        double total_amount
    }
    dim_date {
        int date_id PK
        date date_day
        int year
        int month
        string month_name
        int day_of_month
        int day_of_week
        string day_name
        boolean is_weekend
    }
    dim_zone {
        int zone_id PK
        string borough
        string zone_name
        string service_zone
    }
    dim_payment_type {
        int payment_type_id PK
        string payment_type_name
    }
```

## Layers and why a re-run is safe

| Layer | Where | Re-run behavior |
|---|---|---|
| Download | Airflow DAG `download_tlc_yellow` | Skips a file that exists. Temp file, then rename |
| raw | DuckDB `raw.yellow_trips` | Deletes the month, inserts it again |
| clean | DuckDB `clean.yellow_trips` | Deletes the month, inserts it again |
| analytics | dbt (DuckDB or BigQuery) | dbt rebuilds the tables |
| BigQuery `Taxi.clean_yellow_trips` | `load_bq.py` | First file truncates the table, the rest append |
| Metabase file | `build_metabase_db.py` | Deletes the file, builds it again |

## Scripts

| Script | Role |
|---|---|
| `dags/download_tlc_yellow.py` | Airflow DAG, downloads one month of Parquet |
| `scripts/local/elt.py` | Loads raw, builds clean (dedup and quality rules) |
| `scripts/local/profile.py`, `explore.py` | Look at the data before writing rules |
| `scripts/local/export_marts.py` | Copies the marts into `marts.duckdb` |
| `scripts/local/export_marts_parquet.py` | Exports the marts to Parquet |
| `scripts/local/build_metabase_db.py` | Builds the Metabase file with DuckDB 1.5.6 |
| `scripts/bigquery/export_clean.py` | Exports `clean` to Parquet, one file per month |
| `scripts/bigquery/load_bq.py` | Loads the Parquet files into BigQuery |
| `scripts/bigquery/verify_bq.py`, `check_bq.py` | Compare row counts, check access |

## Notes

- Only the download step runs in Airflow. The other steps are manual scripts.
- The zone lookup CSV is downloaded with `curl` and loaded by `dbt seed`.
- Metabase needs a DuckDB file written by a matching DuckDB version (1.5.6), so it gets its own build step.
- BigQuery sandbox tables expire after 60 days, so that branch is always rebuilt from files.
