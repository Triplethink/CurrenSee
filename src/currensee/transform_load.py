import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Annotated, Any, Optional, cast

import typer
from pydantic import ValidationError

from currensee.config import get_settings
from currensee.constants import (
    API_BASE,
    API_RATES,
    API_TIMESTAMP,
    BASE_CURRENCY,
    DATE,
    RATE,
    TARGET_CURRENCY,
)
from currensee.extract import date_range
from currensee.logging_config import setup_logging
from currensee.models import ExchangeRateRecord
from currensee.storage import LocalStorageWriter

setup_logging()
logger = logging.getLogger('currensee.transform_load')
app = typer.Typer()


@dataclass
class DateRange:
    start_date: date
    end_date: date


@dataclass
class ExecutionOptions:
    dry_run: bool = False
    force_overwrite: bool = False


def read_raw_data(date_str: str, storage_writer: LocalStorageWriter | None = None) -> dict[str, Any]:
    if storage_writer is None:
        storage_writer = LocalStorageWriter()

    file_path_str = storage_writer.get_path(date_str)

    if not Path(file_path_str).exists():
        raise FileNotFoundError(f'No data file found for {date_str} at {file_path_str}')

    try:
        with open(file_path_str) as f:
            data = cast(dict[str, Any], json.load(f))
            return data
    except json.JSONDecodeError as e:
        logger.error(f'Failed to decode JSON from {file_path_str}: {e}')
        raise ValueError(f'Invalid JSON data for {date_str}') from e


def transform_data(raw_data: dict[str, Any]) -> list[ExchangeRateRecord]:
    """Transform raw exchange rate data into a list of Pydantic models."""
    base = raw_data.get(API_BASE, 'USD')
    rates_dict = raw_data.get(API_RATES, {})
    date_str = raw_data.get(DATE)
    if not date_str and API_TIMESTAMP in raw_data:
        date_str = datetime.fromtimestamp(raw_data[API_TIMESTAMP]).strftime('%Y-%m-%d')

    if not date_str:
        raise ValueError('Cannot determine date for raw data')

    if not rates_dict:
        logger.warning(f'No rates found in raw data for date {date_str}')
        return []

    transformed_records = []
    record_date = datetime.strptime(date_str, '%Y-%m-%d').date()

    for currency, rate_value in rates_dict.items():
        try:
            record_data = {
                BASE_CURRENCY: base,
                TARGET_CURRENCY: currency,
                RATE: rate_value,
                DATE: record_date,
            }
            validated_record = ExchangeRateRecord.model_validate(record_data)
            transformed_records.append(validated_record)
        except ValidationError as e:
            logger.error(f'Validation failed for record {currency} on {date_str}: {e}')
            continue

    return transformed_records


def init_database(db_path_str: str) -> None:
    db_path = Path(db_path_str)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path_str)
    cursor = conn.cursor()

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS exchange_rates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        base_currency TEXT NOT NULL,
        target_currency TEXT NOT NULL,
        rate REAL NOT NULL,
        date TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(base_currency, target_currency, date)
    )
    """
    )

    cursor.execute(
        """
    CREATE INDEX IF NOT EXISTS idx_exchange_rates_date
    ON exchange_rates(date)
    """
    )

    cursor.execute(
        """
    CREATE INDEX IF NOT EXISTS idx_exchange_rates_currencies
    ON exchange_rates(base_currency, target_currency)
    """
    )

    conn.commit()
    conn.close()
    logger.info(f'Database schema initialized/verified at {db_path_str}')


def load_data(
    transformed_data: list[ExchangeRateRecord],
    db_path: str,
    date_str: str,
    force_overwrite: bool = False,
    dry_run: bool = False,
) -> int:
    """Load transformed data (Pydantic models) into the database."""
    if not transformed_data:
        logger.info(f'No transformed data to load for {date_str}')
        return 0

    if dry_run:
        logger.info(f'[DRY RUN] Would load {len(transformed_data)} records for {date_str}')
        return len(transformed_data)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    rows_affected = 0

    try:
        conn.execute('BEGIN TRANSACTION')

        if force_overwrite:
            logger.warning(f'Deleting existing data for {date_str} due to force_overwrite')
            cursor.execute('DELETE FROM exchange_rates WHERE date = ?', (date_str,))

        records_to_insert = [
            (
                record.base_currency,
                record.target_currency,
                record.rate,
                record.record_date.strftime('%Y-%m-%d'),
            )
            for record in transformed_data
        ]

        sql = (
            'INSERT INTO exchange_rates (base_currency, target_currency, rate, date) VALUES (?, ?, ?, ?)'
            if force_overwrite
            else 'INSERT OR IGNORE INTO exchange_rates (base_currency, target_currency, rate, date) VALUES (?, ?, ?, ?)'
        )

        cursor.executemany(sql, records_to_insert)
        rows_affected = cursor.rowcount

        if force_overwrite:
            rows_affected = len(records_to_insert)

        conn.commit()
        logger.debug(f'Committed {rows_affected} records for {date_str}')

    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f'Database operation failed for {date_str}: {e}')
        raise
    except Exception as e:
        conn.rollback()
        logger.exception(f'Unexpected error during data load for {date_str}: {e}')
        raise
    finally:
        conn.close()
        logger.debug(f'Database connection closed for {date_str}')

    return rows_affected


def run_transform_load(
    date_range_obj: DateRange,
    options: ExecutionOptions,
    storage_writer: LocalStorageWriter | None = None,
    db_path_str: str | None = None,
) -> dict[str, int]:
    if storage_writer is None:
        storage_writer = LocalStorageWriter()

    settings = get_settings()
    db_path = db_path_str or settings.db_path

    if not options.dry_run:
        init_database(db_path)

    dates_to_process = date_range(date_range_obj.start_date, date_range_obj.end_date)
    result: dict[str, int] = {}

    for current_date in dates_to_process:
        date_str = current_date.strftime('%Y-%m-%d')

        try:
            raw_file_path = Path(storage_writer.get_path(date_str))
            if not raw_file_path.exists():
                logger.warning(f'No raw data file found for {date_str} at {raw_file_path}, skipping...')
                result[date_str] = 0
                continue

            logger.info(f'Processing data for {date_str}')
            raw_data = read_raw_data(date_str, storage_writer)
            transformed_data = transform_data(raw_data)

            if not transformed_data and not options.dry_run:
                logger.info(f'No valid rates transformed for {date_str}, skipping load.')
                result[date_str] = 0
                continue

            rows_affected = load_data(
                transformed_data=transformed_data,
                db_path=db_path,
                date_str=date_str,
                force_overwrite=options.force_overwrite,
                dry_run=options.dry_run,
            )

            result[date_str] = rows_affected
            if not options.dry_run:
                logger.info(f'Successfully processed {rows_affected} records for {date_str}')

        except FileNotFoundError:
            logger.warning(f'Raw data file disappeared for {date_str} between check and read, skipping...')
            result[date_str] = 0
        except ValueError as e:
            logger.error(f'Data validation or processing error for {date_str}: {e}')
            if not options.dry_run:
                raise
        except Exception as e:
            logger.exception(f'Failed to process {date_str}: {e}')
            if not options.dry_run:
                raise

    return result


@app.command()
def main(
    date_from: Annotated[
        Optional[datetime],  # noqa: UP007
        typer.Option(formats=['%Y-%m-%d'], help='Start date in YYYY-MM-DD format. Required if --date-to is set.'),
    ] = None,
    date_to: Annotated[
        Optional[datetime],  # noqa: UP007
        typer.Option(formats=['%Y-%m-%d'], help='End date in YYYY-MM-DD format. Required if --date-from is set.'),
    ] = None,
    db_path: Annotated[
        str, typer.Option('--db-path', help='Path to the SQLite database file (default: from config).')
    ] = get_settings().db_path,
    dry_run: Annotated[
        bool,
        typer.Option('--dry-run', help='Simulate the transform and load operation without modifying the database.'),
    ] = False,
    force_overwrite: Annotated[
        bool, typer.Option('--force-overwrite', help='Overwrite existing data in the database for the specified dates.')
    ] = False,
) -> None:
    """Transform raw data and load it into the database for a given date range.

    If no dates are provided, defaults to today's date for both start and end.
    If either --date-from or --date-to is provided, both must be specified.
    """
    if date_from is None and date_to is None:
        today_date = date.today()
        date_from_date = today_date
        date_to_date = today_date
        logger.info(f'No dates provided, defaulting to today: {today_date.strftime("%Y-%m-%d")}')
    elif date_from is None or date_to is None:
        logger.error('Both --date-from and --date-to must be provided if either is set.')
        raise typer.Exit(code=1)
    else:
        date_from_date = date_from.date()
        date_to_date = date_to.date()

    if date_from_date > date_to_date:
        logger.error(f'Start date {date_from_date} cannot be after end date {date_to_date}.')
        raise typer.Exit(code=1)

    date_range_obj = DateRange(start_date=date_from_date, end_date=date_to_date)
    options = ExecutionOptions(dry_run=dry_run, force_overwrite=force_overwrite)

    result = run_transform_load(
        date_range_obj=date_range_obj,
        options=options,
        db_path_str=db_path,
    )

    total_records = sum(result.values())
    processed_dates_count = len(result)

    if dry_run:
        logger.info(f'[DRY RUN] Would process {total_records} record(s) for {processed_dates_count} date(s)')
    else:
        logger.info(f'Successfully processed {total_records} record(s) for {processed_dates_count} date(s)')


if __name__ == '__main__':
    app()
