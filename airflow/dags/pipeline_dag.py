from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = "/opt/airflow"

default_args = {
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="adzuna_it_job_pipeline",
    default_args=default_args,
    description="Extract IT jobs from Adzuna API, classify AI-related roles, and stage data for Postgres loading.",
    schedule="@weekly",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["adzuna", "etl"],
) as dag:

    extract = BashOperator(
        task_id="extract_it_jobs",
        bash_command=f"cd {PROJECT_DIR} && python src/extract/adzuna_IT_job_extract.py",
    )

    classify = BashOperator(
        task_id="classify_ai_roles",
        bash_command=f"cd {PROJECT_DIR} && python src/cleaning/ai_identifier.py",
    )

    stage = BashOperator(
        task_id="stage_data",
        bash_command=f"cd {PROJECT_DIR} && python src/cleaning/data_cleaning.py",
    )

    load = BashOperator(
        task_id="load_data_to_postgres",
        bash_command=f"cd {PROJECT_DIR} && python src/load/load_to_postgres.py"
    )

    extract >> classify >> stage >> load
