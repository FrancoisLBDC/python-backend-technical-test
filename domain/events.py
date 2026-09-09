from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from domain.entities import Currency


@dataclass(frozen=True)
class ExchangeRateChanged:
    currency: Currency
    previous_rate: Decimal | None
    new_rate: Decimal
    as_of: datetime
    occurred_at: datetime
