"""Extraction module for fetching exchange rate data from OpenExchangeRates API."""
import json
import logging
from datetime import date, datetime, timedelta
from typing import Annotated, Any, Optional, cast

import requests
import typer
from pydantic import ValidationError
from requests.exceptions import RequestException

from currensee.config import get_settings
from currensee.logging_config import setup_logging
from currensee.models import OpenExchangeRatesResponse
from currensee.storage import LocalStorageWriter, StorageWriter

setup_logging()
logger = logging.getLogger('currensee.extract')
app = typer.Typer()


class OpenExchangeRatesClient:
    """OpenExchangeRates API client for fetching latest and historical rates.

    API documentation:
    - Latest rates: https://openexchangerates.org/api/latest
    - Historical rates: https://openexchangerates.org/api/historical/
    """

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.oe_api_key
        self.base_url = base_url or settings.oe_api_base_url

    def get_exchange_rates(self, date_str: str, base: str = 'USD') -> OpenExchangeRatesResponse:
        today = date.today().strftime('%Y-%m-%d')

        if date_str == today:
            endpoint = f'{self.base_url}/latest.json'
            logger.info("Using latest endpoint for today's rates")
        else:
            endpoint = f'{self.base_url}/historical/{date_str}.json'
            logger.info(f'Using historical endpoint for {date_str}')

        params = {'app_id': self.api_key, 'base': base}

        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            raw_data = cast(dict[str, Any], response.json())

            validated_data: OpenExchangeRatesResponse = OpenExchangeRatesResponse.model_validate(raw_data)
            validated_data.date_str = date_str
            return validated_data

        except RequestException as e:
            logger.error(f'API request failed for {date_str}: {e}')
            raise ValueError(f'API request failed: {e}') from e
        except ValidationError as e:
            logger.error(f'API response validation failed for {date_str}: {e}')
            raise ValueError(f'Invalid API response format: {e}') from e
        except json.JSONDecodeError as e:
            logger.error(f'Failed to decode API response JSON for {date_str}: {e}')
            raise ValueError(f'Invalid JSON received from API: {e}') from e


def date_range(start_date: date, end_date: date) -> list[date]:
    if start_date > end_date:
        raise ValueError('Start date cannot be after end date')
    delta = (end_date - start_date).days + 1
    return [start_date + timedelta(days=i) for i in range(delta)]


def run_extraction(
    date_from: date,
    date_to: date,
    dry_run: bool = False,
    force_overwrite: bool = False,
    storage_writer: StorageWriter | None = None,
) -> dict[str, str]:
    if storage_writer is None:
        storage_writer = LocalStorageWriter()

    client = OpenExchangeRatesClient()
    dates_to_process = date_range(date_from, date_to)
    result: dict[str, str] = {}

    for current_date in dates_to_process:
        date_str = current_date.strftime('%Y-%m-%d')

        try:
            if storage_writer.exists(date_str) and not force_overwrite:
                logger.info(f'Data for {date_str} already exists, skipping...')
                result[date_str] = storage_writer.get_path(date_str)
                continue

            if dry_run:
                logger.info(f'[DRY RUN] Would fetch exchange rates for {date_str}')
                result[date_str] = storage_writer.get_path(date_str)
                continue
            else:
                logger.info(f'Fetching exchange rates for {date_str}')
                data_model = client.get_exchange_rates(date_str)
                data_dict = data_model.model_dump(by_alias=True)
            path = storage_writer.write(
                data=data_dict,
                date_str=date_str,
                force_overwrite=force_overwrite,
                dry_run=dry_run,
            )

            result[date_str] = path
            logger.info(f'Successfully saved exchange rates for {date_str} to {path}')

        except ValueError as e:
            logger.error(f'Failed to process {date_str}: {e}')
            if not dry_run:
                raise
        except Exception as e:
            logger.exception(f'Unexpected extraction job failure: {e}')
            if not dry_run:
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
    dry_run: Annotated[
        bool, typer.Option('--dry-run', help='Simulate the extraction without actually fetching or writing data.')
    ] = False,
    force_overwrite: Annotated[bool, typer.Option('--force-overwrite', help='Overwrite existing data files.')] = False,
) -> None:
    """Extract exchange rates from OpenExchangeRates API for a given date range.

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

    try:
        result = run_extraction(
            date_from=date_from_date,
            date_to=date_to_date,
            dry_run=dry_run,
            force_overwrite=force_overwrite,
        )

        if dry_run:
            logger.info(f'[DRY RUN] Would process {len(result)} date(s)')
        else:
            logger.info(f'Successfully processed {len(result)} date(s)')

    except ValueError as e:
        logger.error(f'Extraction job failed: {e}')
        raise typer.Exit(code=1) from e
    except Exception as e:
        logger.exception(f'Unexpected extraction job failure: {e}')
        raise typer.Exit(code=1) from e


if __name__ == '__main__':
    app()
