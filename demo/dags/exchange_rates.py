import datetime
from decimal import Decimal
from typing import TypedDict

import requests
from airflow.decorators import dag, task
from airflow.models import DAG, DagRun, Variable, XCom
from airflow.providers.amazon.aws.operators.s3 import S3CreateObjectOperator
from airflow.utils.session import create_session


class CurrencyPair(TypedDict):
    base: str
    counter: str


class ExchangeRate(TypedDict):
    pair: CurrencyPair
    date: datetime.date
    value: Decimal


@dag(
    start_date=datetime.datetime(year=2023, month=7, day=1),
    schedule_interval="@once",
    catchup=False,
    max_active_runs=1,
)
def exchange_rates():
    @task
    def extract_rates(
        pair: CurrencyPair,
        # Default values are required to avoid a TypeError.
        dag: DAG = None,
        ds: str = None,
    ) -> ExchangeRate:
        """
        Extract rates from the Exchange Rates API
        and convert them to a structured format.
        """
        response = requests.get(
            # Extract API endpoint from Variable
            # with the same name as the DAG ID.
            url=Variable.get(dag.dag_id).get("endpoint"),
            params={
                "from": pair["base"],
                "to": pair["counter"],
                "date": ds,
            },
        )
        content = response.json()
        return ExchangeRate(
            pair=CurrencyPair(
                base=content["query"]["from"],
                counter=content["query"]["to"],
            ),
            date=datetime.date.fromisoformat(content["date"]),
            value=Decimal(content["result"]),
        )

    @task
    def merge_rates(rates: list[ExchangeRate]) -> str:
        """
        Merge the extracted rates into a single CSV-formatted string.
        """
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["base", "counter", "date", "rate"])
        writer.writerows(
            [
                rate["pair"]["base"],
                rate["pair"]["counter"],
                rate["date"].strftime("%Y-%m-%d"),
                str(rate["value"].normalize()),
            ]
            for rate in rates
        )

        return output.getvalue()

    # Upload the merged rates to S3.
    upload_rates = S3CreateObjectOperator(
        task_id="upload_rates",
        aws_conn_id="minio",
        s3_bucket="storage",
        s3_key="exchange_rates/{{ ds }}.csv",
        data="{{ task_instance.xcom_pull(task_ids='merge_rates') }}",
        replace=True,
    )

    # Clean up artifacts from the XCom including
    # the extracted rates and the merged rates.
    @task
    def clean_xcom(**kwargs) -> None:
        dag_run: DagRun = kwargs["dag_run"]
        with create_session() as session:
            session.query(XCom).filter(
                XCom.dag_id == dag_run.dag_id,
                XCom.run_id == dag_run.run_id,
            ).delete()

    (
        merge_rates(
            extract_rates.expand(
                # Expand to create a dedicated task for each currency pair.
                pair=[
                    CurrencyPair(base="USD", counter="CAD"),
                    CurrencyPair(base="EUR", counter="USD"),
                    CurrencyPair(base="USD", counter="CHF"),
                    CurrencyPair(base="GBP", counter="USD"),
                    CurrencyPair(base="NZD", counter="USD"),
                ]
            )
        )
        >> upload_rates
        >> clean_xcom()
    )


exchange_rates()
