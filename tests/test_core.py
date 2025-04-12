import json
from datetime import date, datetime
from pathlib import Path

import pytest

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
from currensee.models import ExchangeRateRecord, OpenExchangeRatesResponse
from currensee.storage import LocalStorageWriter
from currensee.transform_load import transform_data

USD_CURRENCY = 'USD'
EUR_CURRENCY = 'EUR'
GBP_CURRENCY = 'JPY'
TEST_RATE_EUR = 0.85
TEST_RATE_GBP = 0.75
TEST_RATE_JPY = 115.5
TEST_TIMESTAMP = 1744704000  # 2025-04-15
TEST_DATE_COUNT = 5
TEST_RECORD_COUNT = 3


class TestModels:
    def test_exchange_rate_record_validation(self):
        valid_data = {
            BASE_CURRENCY: USD_CURRENCY,
            TARGET_CURRENCY: EUR_CURRENCY,
            RATE: TEST_RATE_EUR,
            DATE: date(2025, 4, 15),
        }
        record = ExchangeRateRecord.model_validate(valid_data)
        assert record.base_currency == USD_CURRENCY
        assert record.target_currency == EUR_CURRENCY
        assert record.rate == TEST_RATE_EUR
        assert record.record_date == date(2025, 4, 15)

        invalid_data = {
            BASE_CURRENCY: USD_CURRENCY,
            TARGET_CURRENCY: EUR_CURRENCY,
            # Missing RATE
            DATE: date(2025, 4, 15),
        }
        with pytest.raises(ValueError):  # More specific than Exception
            ExchangeRateRecord.model_validate(invalid_data)

    def test_open_exchange_rates_response_validation(self):
        valid_data = {
            API_TIMESTAMP: TEST_TIMESTAMP,
            API_BASE: USD_CURRENCY,
            API_RATES: {EUR_CURRENCY: TEST_RATE_EUR, 'GBP': TEST_RATE_GBP},
        }
        response = OpenExchangeRatesResponse.model_validate(valid_data)
        assert response.base == USD_CURRENCY
        assert response.rates == {EUR_CURRENCY: TEST_RATE_EUR, 'GBP': TEST_RATE_GBP}
        assert response.timestamp == TEST_TIMESTAMP

        invalid_data = {
            API_TIMESTAMP: TEST_TIMESTAMP,
            API_BASE: USD_CURRENCY,
            API_RATES: {},  # Empty rates (should fail validation)
        }
        with pytest.raises(ValueError):  # More specific than Exception
            OpenExchangeRatesResponse.model_validate(invalid_data)


class TestDateRange:
    def test_date_range_generation(self):
        start = date(2025, 4, 15)
        end = date(2025, 4, 19)
        dates = date_range(start, end)

        assert len(dates) == TEST_DATE_COUNT
        assert dates[0] == date(2025, 4, 15)
        assert dates[-1] == date(2025, 4, 19)

        single_day = date_range(start, start)
        assert len(single_day) == 1
        assert single_day[0] == start

        with pytest.raises(ValueError):
            date_range(end, start)  # end before start


class TestStorage:
    @pytest.fixture
    def mock_storage_writer(self, tmp_path):
        base_path = str(tmp_path)
        stage_dir = 'stage/test'
        return LocalStorageWriter(base_path=base_path, stage_dir=stage_dir)

    def test_storage_path_generation(self, mock_storage_writer):
        date_str = '2025-04-15'
        path = mock_storage_writer.get_path(date_str)

        # Path should contain base path, stage dir and date
        assert date_str in path
        assert 'stage/test' in path

    def test_storage_write(self, mock_storage_writer):
        test_data = {'test': 'data'}
        date_str = '2025-04-15'

        path = mock_storage_writer.write(test_data, date_str)
        assert Path(path).exists()

        with open(path) as f:
            saved_data = json.load(f)
        assert saved_data == test_data

        assert mock_storage_writer.exists(date_str)

        with pytest.raises(FileExistsError):
            mock_storage_writer.write(test_data, date_str)

        path2 = mock_storage_writer.write({'new': 'data'}, date_str, force_overwrite=True)
        assert path == path2
        with open(path) as f:
            new_data = json.load(f)
        assert new_data == {'new': 'data'}


class TestTransform:
    def test_transform_data(self):
        raw_data = {
            API_BASE: USD_CURRENCY,
            API_TIMESTAMP: TEST_TIMESTAMP,  # 2025-04-15
            API_RATES: {EUR_CURRENCY: TEST_RATE_EUR, 'GBP': TEST_RATE_GBP, 'JPY': TEST_RATE_JPY},
        }

        transformed = transform_data(raw_data)

        assert len(transformed) == TEST_RECORD_COUNT

        currencies = [r.target_currency for r in transformed]
        assert EUR_CURRENCY in currencies
        assert 'GBP' in currencies
        assert 'JPY' in currencies

        eur_record = next(r for r in transformed if r.target_currency == EUR_CURRENCY)
        assert eur_record.base_currency == USD_CURRENCY
        assert eur_record.rate == TEST_RATE_EUR
        assert eur_record.record_date == datetime.fromtimestamp(TEST_TIMESTAMP).date()
