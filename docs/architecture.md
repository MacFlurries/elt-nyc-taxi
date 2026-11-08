# Arsitektur D1: NYC Taxi ELT

```mermaid
%%{init: {"theme":"base","themeVariables":{"fontFamily":"Inter, Segoe UI, sans-serif","fontSize":"16px","lineColor":"#64748b","textColor":"#1e293b","edgeLabelBackground":"#f8fafc"},"flowchart":{"curve":"basis","nodeSpacing":30,"rankSpacing":45,"padding":12}}}%%
flowchart TB
    TLC(["🗽 <b>NYC TLC</b><br/>Yellow Taxi Parquet"]):::source
    RAWF[("📁 <b>data/raw</b><br/>file Parquet")]:::storage

    TLC -->|"Airflow DAG<br/>1 bulan per run"| RAWF

    subgraph DUCK["🦆 Jalur Lokal · DuckDB"]
        direction TB
        RAW[("🥉 <b>raw</b><br/>yellow_trips")]:::raw
        CLEAN[("🥈 <b>clean</b><br/>yellow_trips")]:::clean
        MARTS["🥇 <b>analytics</b><br/>stg_yellow_trips<br/>dim_zone · dim_payment_type<br/>dim_date · fct_trips"]:::mart
        RAW -->|"dedup + aturan kualitas"| CLEAN
        CLEAN -->|"dbt · dev"| MARTS
    end

    RAWF -->|"elt.py"| RAW

    MARTS -->|"export Parquet +<br/>build_metabase_db.py"| MBDB[("🗄️ <b>marts.duckdb</b>")]:::storage
    MBDB --> MB(["📈 <b>Metabase</b><br/>Dashboard NYC Taxi"]):::bi

    subgraph BQ["☁️ Jalur Cloud · BigQuery"]
        direction TB
        BQC[("🥈 <b>clean</b><br/>Taxi.clean_yellow_trips")]:::clean
        BQM["🥇 <b>analytics</b><br/>stg + dim_* + fct_trips"]:::mart
        BQC -->|"dbt · bq"| BQM
    end

    CLEAN -->|"export_clean.py<br/>+ load_bq.py"| BQC

    classDef source  fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#075985
    classDef storage fill:#f1f5f9,stroke:#64748b,stroke-width:2px,color:#334155
    classDef raw     fill:#ffedd5,stroke:#ea580c,stroke-width:2px,color:#9a3412
    classDef clean   fill:#e2e8f0,stroke:#475569,stroke-width:2px,color:#1e293b
    classDef mart    fill:#fef9c3,stroke:#ca8a04,stroke-width:2px,color:#713f12
    classDef bi      fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#14532d

    style DUCK fill:#fffbeb,stroke:#f59e0b,stroke-width:2px,stroke-dasharray:5 5,color:#92400e
    style BQ   fill:#eff6ff,stroke:#3b82f6,stroke-width:2px,stroke-dasharray:5 5,color:#1e3a8a
```
