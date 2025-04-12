# Solution Description
Here I'm answering all the answers from the assignment as well as my design decisions.

## 1. Evaluate market options
- the whole process of choosing the best provider is described in the [Evaluation Document](docs/EVALUATION.md) file.
- in short, the winner for me was [Open Exchange Rates](https://openexchangerates.org) as it has free tier with:
    - hourly and daily values
    - historical values
    - enought request calls
    - good API health and monitoring/alerting options
- **the risk** could be trusting just one provider, in my solution we can use as a fallback solution the last data from our local storage, but in the production ready solution we could think about some other (free) provider which will be ready just in case.

## 2. Develop an extraction, transformation, and load module/s
- I've decided for ETL rather than ELT approach for the following reasons:
    - Rates are small and fast to transform.
    - The transformation logic is straightforward and doesn't require the computational power of a database engine.
    - Transforming before loading ensures data is consistent and validated before entering the database.

## 3. Module readiness
- description of my solution:
    - budget efficient
    - two jobs, one for extracting one for transform and load.
    -
- best practices I've used:
    - robust logging
    - data validation using pydantic
    - pre-commit hooks, linters and formaters
    - (at leas some) unit tests
    - typer library for CLI (I just wanted to try it)
    - modularity, e.g. some other writers (S3) could be easily added
    - the selected data provider could be relatively easily switch to some other REST API.
    - the solution allows reprocessing of the data and doing dry-runs, which could help with adding new features


## 4. Deployment and integration:
- Deploying
    - I would put it on CR -> after CROK -> deploy to dev
    - test it there
    - scheduled it in Airflow on daily basis with some retry strategy (would be part of the CR on the start)
    - I would add description of the table and its columns to some internal database.

- Integration into Broader Data Model
    - Final currency rates go to `exchange_rate` table.
    - key for this table is: `` which will be the most efficient to use for join
    - updated once per day via insert
    - the table is joinable with transactions ( e.g. something like `fact_payments`, `fact_orders`) and financial reports
    - exposed via some BI layer
- Communication of this project is described in [Communication Document](docs/COMMUNICATION.md) file.
- the potential value of the final data to the organization:
    - Accurate Financial Reporting and Analysis
    - improvement for BI team
    - Operational Efficiency (eliminates manual effort)
    - historical data could help Anal. team to predict effects of accepting different currencies even with the volatility of the currency

## BONUS: Limitation and potential improvements of my solution
- I should add a second fallback data provider (could be some free bank api with daily data only)
- no alerts set, but I think the company has already some standards for it
- no anomaly detection, again I expect here some Grafana alerts or custom logic in company
- If your company is using a tool like Snowflake, maybe just extraction job will be needed
- maybe we can add some rounding for the decimals if we don't need that detailed precision.
- I would maybe save the data with some natural key, like the combination of base_currency, target_currency, date instead of the default index.
- not 100% test coverage
