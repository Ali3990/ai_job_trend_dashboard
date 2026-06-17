from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = "/opt/airflow"

default_args = {
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="placer_migration_zcta_load",
    default_args=default_args,
    description="Bulk load of Placer.ai ZCTA net migration data into Postgres.",
    schedule=None,
    start_date=datetime(2026, 6, 17),
    catchup=False,
    max_active_runs=1,
    tags=["migration", "placer", "railway postgres"],
) as dag:

    load = BashOperator(
        task_id="load_migration_to_postgres",
        bash_command=f"cd {PROJECT_DIR} && python src/load/load_placer_postgres.py",
    )
