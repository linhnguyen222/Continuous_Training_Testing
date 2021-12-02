import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)
from datetime import datetime, timedelta
from textwrap import dedent
from airflow import DAG
from airflow.operators.python import PythonOperator
from server.server import *
from data_streaming.data_streaming import *
print(os.getcwd())
def handle_failure():
    print("Opps")
    handle_server()
    handle_streaming_data()


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['nguyenmylinh.9720@gmail.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
    'start_date': datetime(2021, 11, 22),
    # 'queue': 'bash_queue',
    # 'pool': 'backfill',
    # 'priority_weight': 10,
    'end_date': datetime(2021, 12, 10),
    # 'wait_for_downstream': False,
    # 'dag': dag,
    # 'sla': timedelta(hours=2),
    # 'execution_timeout': timedelta(seconds=300),
    'on_failure_callback': handle_failure,
}

with DAG(
    'bts_static_dag2',
    default_args=default_args,
    description='Benchmark application',
    schedule_interval=timedelta(days=1),
) as dag:
    static_server = PythonOperator(
        task_id = "bts_static_server",
        python_callable = handle_server,
    )
    data_streaming = PythonOperator(
        task_id = "bts_data_streaming",
        python_callable = handle_streaming_data,
    )
    static_server
    data_streaming


