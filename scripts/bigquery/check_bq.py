import os
from google.cloud import bigquery

client = bigquery.Client(project=os.environ["GCP_PROJECT_ID"])
for d in client.list_datasets():
    print(d.dataset_id)