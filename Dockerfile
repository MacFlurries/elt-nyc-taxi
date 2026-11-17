FROM apache/airflow:3.3.2
RUN python -m venv /home/airflow/dbt-venv \
 && /home/airflow/dbt-venv/bin/pip install --no-cache-dir \
    dbt-core==1.12.6 dbt-duckdb==1.11.1 duckdb==2.0.0
