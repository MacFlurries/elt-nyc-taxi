import os
import urllib.request

import pendulum
from airflow.sdk import dag, task

BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"
RAW_DIR = "/opt/airflow/data/raw"


@dag(
    dag_id="download_tlc_yellow",
    schedule="@monthly",
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    end_date=pendulum.datetime(2025, 3, 31, tz="UTC"),
    catchup=True,
    max_active_runs=1,
    tags=["d1", "tlc"],
)
def download_tlc_yellow():
    @task
    def download(data_interval_start=None):
        month = data_interval_start.strftime("%Y-%m")
        name = f"yellow_tripdata_{month}.parquet"
        final = os.path.join(RAW_DIR, name)
        os.makedirs(RAW_DIR, exist_ok=True)

        if os.path.exists(final): 
            print(f"SKIP: {name} sudah ada")
            return final

        tmp = final + ".tmp"  # file sementara
        urllib.request.urlretrieve(f"{BASE_URL}/{name}", tmp)
        os.replace(tmp, final)
        print(f"OK: {name} ({os.path.getsize(final)} bytes)")
        return final

    download()


download_tlc_yellow()