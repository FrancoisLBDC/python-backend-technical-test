from collections.abc import Iterable
from typing import Protocol

from domain.entities import Currency, ExchangeRate


class ExchangeRateRepository(Protocol):
    def get_rate(self, currency: Currency) -> ExchangeRate:
        """Return the most recent rate for `currency`.

        Raises RateNotFound if none exists. Never called for
        domain.entities.REFERENCE_CURRENCY -- callers treat its rate as the
        known identity value instead of looking it up here.
        """
        ...

    def save_rate(self, rate: ExchangeRate) -> None:
        """Upsert `rate`."""
        ...

    def save_many(self, rates: Iterable[ExchangeRate]) -> None:
        """Upsert every rate in `rates`."""
        ...
