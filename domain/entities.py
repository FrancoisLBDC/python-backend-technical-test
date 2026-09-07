import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from domain.exceptions import UnknownCurrency

_CURRENCY_CODE_PATTERN = re.compile(r"^[A-Z]{3}$")


@dataclass(frozen=True)
class Currency:
    code: str

    def __post_init__(self) -> None:
        normalized = self.code.upper()
        if not _CURRENCY_CODE_PATTERN.match(normalized):
            raise UnknownCurrency(f"'{self.code}' is not a valid ISO currency code")
        object.__setattr__(self, "code", normalized)


REFERENCE_CURRENCY = Currency("EUR")


@dataclass(frozen=True)
class ExchangeRate:
    currency: Currency
    # Value of 1 EUR expressed in `currency`.
    versus_euro_rate: Decimal
    as_of: datetime


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: Currency
