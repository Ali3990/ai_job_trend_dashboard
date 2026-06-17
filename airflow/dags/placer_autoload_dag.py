import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sensors.python import PythonSensor

PROJECT_DIR = "/opt/airflow"
TRIGGER_FILE = f"{PROJECT_DIR}/pipeline_data/migration_zcta_net.trigger"

default_args = {
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}


def _trigger_file_exists() -> bool:
    return os.path.exists(TRIGGER_FILE)


with DAG(
    dag_id="migration_zcta_load",
    default_args=default_args,
    description="Auto-loads Placer.ai ZCTA migration data when trigger file is detected.",
    schedule="*/5 * * * *",
    start_date=datetime(2026, 6, 17),
    catchup=False,
    max_active_runs=1,
    tags=["migration", "placer", "railway postgres"],
) as dag:

    wait_for_trigger = PythonSensor(
        task_id="wait_for_trigger_file",
        python_callable=_trigger_file_exists,
        poke_interval=60,
        timeout=240,
        mode="reschedule",
        soft_fail=True,
    )

    load = BashOperator(
        task_id="load_migration_to_postgres",
        bash_command=f"cd {PROJECT_DIR} && python src/load/load_placer_postgres.py",
    )

    cleanup = BashOperator(
        task_id="remove_trigger_file",
        bash_command=f"rm -f {TRIGGER_FILE}",
    )

    wait_for_trigger >> load >> cleanup
