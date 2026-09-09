from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from domain.entities import Currency, Money


@dataclass(frozen=True)
class ParsedQuery:
    amount: Decimal
    source_currency: Currency
    target_currency: Currency


@dataclass(frozen=True)
class ConversionResult:
    source: Money
    converted: Money


@dataclass(frozen=True)
class ImportSummary:
    imported_count: int
    as_of: datetime
