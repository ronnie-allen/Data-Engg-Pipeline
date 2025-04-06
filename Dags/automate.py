from airflow import DAG
from airflow.operators.dummy import DummyOperator
from datetime import datetime

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
}

with DAG(
    dag_id='dummy_water_quality_pipeline',
    default_args=default_args,
    description='A dummy DAG to simulate water quality processing',
    schedule_interval='@daily',
    catchup=False,
    tags=['demo', 'water-quality'],
) as dag:

    start = DummyOperator(task_id='start')

    check_data = DummyOperator(task_id='check_data_available')

    process_data = DummyOperator(task_id='process_water_quality_data')

    end = DummyOperator(task_id='end')

    # DAG structure
    start >> check_data >> process_data >> end
