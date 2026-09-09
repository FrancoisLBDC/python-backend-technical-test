from typing import Protocol

from domain.entities import ExchangeRate


class ExchangeRateSource(Protocol):
    def fetch_rates(self) -> list[ExchangeRate]:
        """Fetch the latest known exchange rates from an external source."""
        ...
