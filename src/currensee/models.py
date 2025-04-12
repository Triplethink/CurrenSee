from datetime import date
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

from currensee.constants import (
    API_BASE,
    API_RATES,
    API_TIMESTAMP,
    BASE_CURRENCY,
    DATE,
    RATE,
    TARGET_CURRENCY,
)


class ExchangeRateRecord(BaseModel):
    base_currency: str = Field(..., alias=BASE_CURRENCY)
    target_currency: str = Field(..., alias=TARGET_CURRENCY)
    rate: float = Field(..., alias=RATE)
    record_date: date = Field(..., alias=DATE)

    model_config: ClassVar[ConfigDict] = ConfigDict(populate_by_name=True)


class OpenExchangeRatesResponse(BaseModel):
    disclaimer: str | None = None
    license: str | None = None
    timestamp: int = Field(..., alias=API_TIMESTAMP)
    base: str = Field(..., alias=API_BASE)
    rates: dict[str, float] = Field(..., alias=API_RATES)
    date_str: str | None = Field(None, alias=DATE)

    @field_validator('rates')
    def check_rates_not_empty(cls, v: dict[str, float]) -> dict[str, float]:  # noqa: N805
        if not v:
            raise ValueError('API response rates dictionary cannot be empty')
        return v

    model_config: ClassVar[ConfigDict] = ConfigDict(populate_by_name=True, extra='ignore')
