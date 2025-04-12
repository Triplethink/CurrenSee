# CurrenSee

ETL pipeline for currency exchange rates from Open Exchange Rates API.

This is a home assignment solution by me (Robert W.)

**IMPORTANT:**
All the answers from the assignment should be answered in [Solution Description](docs/SOLUTION_DESCRIPTION.md).
As I wanted to add even some biger context how I was thining about the project I'm attaching also [Communication Document](docs/COMMUNICATION.md). The last important fiel is [Evaluation Document](docs/EVALUATION.md) which should answer the question why I've chosen Open Exchange Rates API.

## Features of my implementation

- Daily exchange rate data extraction from Open Exchange Rates API
- Optimized API usage: `/latest` endpoint for current day and `/historical` for past dates
- Raw data storage in JSON format with date-based organization
- Transformation of raw data into flat tabular structure
- kinda ACID-compliant loading into SQLite database
- Support for incremental loading and backfilling historical data
- Parameterized jobs with date range, dry run, and force overwrite options
- Modern path handling with Pathlib for better cross-platform compatibility
- Extensible storage abstraction (local filesystem with design for S3 compatibility)

## Installation

### Prerequisites

- Python 3.10 or newer
- Poetry (dependency management)

### Setup

1. Clone the repository:
2. Install dependencies using Poetry

```bash
poetry install
```

3. Create a `.env` file based on the provided `.env.example`:

```bash
cp .env.example .env
```

4. Edit the `.env` file to include your Open Exchange Rates API key:

```bash
OE_API_KEY=your_api_key_here
```

You can get your API key from [this page](https://openexchangerates.org/signup/free)

5. OPTIONAL: Set up pre-commit hooks:

```bash
poetry run pre-commit install
```

## Usage

> Doublecheck that you created the environment via Poetry.

As it has also CLI features (just for fun, I wanted to try Typer), you can always use: `python -m currensee.extract --help` or `python3 -m currensee.transform_load --help`

### Extraction Job

The extraction job fetches exchange rate data from the Open Exchange Rates API and stores it as raw JSON files.

```bash
python3 -m currensee.extract --date-from 2025-04-13 --date-to 2025-04-15
```

Other options:
- add `--dry-run` to simulate execution without making API calls or writing files
- add `--force-overwrite` to overwrite of existing files
- you can not provide `--date-from` an `--date-to` and it will automatically fallback to todays date


### Transform and Load Job

The transform and load job reads the raw JSON files, transforms the data into a flat structure, and loads it into a SQLite database.

```bash
python3 -m src.currensee.transform_load --date-from 2025-04-13 --date-to 2025-04-15
```
Other options:
- add `--dry-run` to simulate without writing to database
- add `--force-overwrite` to overwrite of existing data in database
- add `--db-path /custom/path/exchange_rates.db` to specify custom database path
- you can not provide `--date-from` an `--date-to` and it will automatically fallback to todays date

### SQLite Database Interaction

The exchange rate data is stored in a SQLite database. You can interact with it using the `sqlite3` command line tool:

```bash
# Open the database
sqlite3 data/exchange_rates.db

# View all tables
.tables

# View schema
.schema exchange_rates

# Run a sample query
SELECT * FROM exchange_rates WHERE date = '2025-04-15' LIMIT 5;

# Export query results to CSV
.mode csv
.output rates.csv
SELECT * FROM exchange_rates WHERE date BETWEEN '2025-04-13' AND '2025-04-15';
.output stdout
```

## Configuration

The application is configured using environment variables, which can be set directly or through a `.env` file.

| Variable | Description | Default |
|----------|-------------|---------|
| `OE_API_KEY` | OpenExchangeRates API key (required) | - |
| `OE_API_BASE_URL` | OpenExchangeRates API base URL | https://openexchangerates.org/api |
| `STORAGE_BASE_PATH` | Base path for storage | [project_root]/data |
| `STAGE_DIR` | Directory for staged raw data | /stage/exchange-rates/daily |
| `DB_PATH` | Path to SQLite database | data/exchange_rates.db |
