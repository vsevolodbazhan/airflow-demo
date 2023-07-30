# Airflow Demo Project

Airflow-based demo pipeline that extracts currency exchange rates and
and stores them in an S3-compatible storage. The goal of this demo is to provide a complete, production-like pipeline
on which to base tutorials and blog posts.

## Walkthrough

### Setup

Docker Compose is used to setup the Airflow instance and supportive services (such as Minio).

- `airflow-database`: a PostgreSQL database that is used to store Airflow's metadata.
- `airflow-init`: a service that is used to initialize the Airflow database and create admin user.
- `airflow-scheduler`: a service that runs the Airflow scheduler.
- `airflow-webserver`: a service that runs the Airflow webserver.
- `storage`: a Minio server that is used to store Airflow artifacts.
- `storage-init`: a service that is used to initialize the Minio server and create a bucket named `storage`.

To run the Docker Compose file, you can use the following command:
```
docker-compose up
```

This will start all of the services in the Docker Compose file. You can then access the Airflow webserver at `http://localhost:8080`.

This demo's Airflow instances used `LocalExecutor` and runs its task directly in `airflow-scheduler` container.

`LocalFilesystemBackend` is used to store Connecitons and Variables. Note that you will note be able to see those items in the Airflow Webserver UI.

### DAG

This DAG extracts exchange rates from the Exchange Rates API and uploads them to S3.

- `extract_rates` task extracts exchange rates for a given currency pair.
- `merge_rates` merges the extracted rates into a single CSV-formatted string.
- `upload_rates` uploads the merged rates to S3.
- `clean_xcom` cleans up artifacts from the XCom, including the extracted rates and the merged rates.

Here are some additional notes about the DAG:

- The DAG uses the `TypedDict` type to define the structure of the exchange rate data. This makes the code more concise and easier to read.
- The DAG uses the expand operator to create a dedicated task for each currency pair. This allows the DAG to be more scalable, as it can be easily extended to support additional currency pairs.
- The DAG uses the `clean_xcom` task to clean up artifacts from the XCom. This is important to do, as the XCom can grow in size over time and can impact the performance of the DAG.

To run this DAG simply toggle it in the Airflow Webserver UI.

## License

MIT License

Copyright (c) 2023 Vsevolod Bazhan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
