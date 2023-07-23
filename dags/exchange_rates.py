import datetime
from decimal import Decimal
from typing import TypedDict

import requests
from airflow.decorators import dag, task


class CurrencyPair(TypedDict):
    base: str
    counter: str


class ExchangeRate(TypedDict):
    pair: CurrencyPair
    date: datetime.date
    value: Decimal


@dag(
    start_date=datetime.datetime(year=2023, month=7, day=1),
    schedule_interval=None,
    catchup=True,
    max_active_runs=1,
)
def exchange_rates():
    @task
    def extract_rates(pair: CurrencyPair, **kwargs) -> ExchangeRate:
        response = requests.get(
            url="https://api.exchangerate.host/convert",
            params={
                "from": pair["base"],
                "to": pair["counter"],
                "date": kwargs["ds"],
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

    merge_rates(
        extract_rates.expand(
            pair=[
                CurrencyPair(base="USD", counter="EUR"),
                CurrencyPair(base="USD", counter="GBP"),
                CurrencyPair(base="USD", counter="THB"),
                CurrencyPair(base="USD", counter="SGD"),
            ]
        )
    )


exchange_rates()
