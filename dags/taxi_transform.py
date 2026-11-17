import pendulum
from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator

VENV = "/home/airflow/dbt-venv/bin"
DBT = f"cd /opt/airflow/dbt_taxi && {VENV}/dbt"

with DAG(
    dag_id="taxi_transform",
    schedule=None,
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    tags=["d1", "tlc"],
) as dag:
    raw_clean = BashOperator(
        task_id="raw_clean",
        bash_command=f"cd /opt/airflow && {VENV}/python scripts/local/elt.py",
    )
    dbt_seed = BashOperator(
        task_id="dbt_seed",
        bash_command=f"{DBT} seed --profiles-dir . --target dev",
    )
    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"{DBT} run --profiles-dir . --target dev",
    )
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"{DBT} test --profiles-dir . --target dev",
    )
    raw_clean >> dbt_seed >> dbt_run >> dbt_test
