from collections.abc import Iterable

from domain.entities import Currency, ExchangeRate
from domain.exceptions import RateNotFound


class FakeExchangeRateRepository:
    def __init__(self, rates: dict[str, ExchangeRate] | None = None) -> None:
        self._rates: dict[str, ExchangeRate] = dict(rates or {})
        self.saved: list[ExchangeRate] = []

    def get_rate(self, currency: Currency) -> ExchangeRate:
        try:
            return self._rates[currency.code]
        except KeyError:
            raise RateNotFound(f"No rate found for {currency.code}") from None

    def save_rate(self, rate: ExchangeRate) -> None:
        self._rates[rate.currency.code] = rate
        self.saved.append(rate)

    def save_many(self, rates: Iterable[ExchangeRate]) -> None:
        for rate in rates:
            self.save_rate(rate)


class FakeExchangeRateSource:
    def __init__(self, rates: list[ExchangeRate]) -> None:
        self._rates = rates

    def fetch_rates(self) -> list[ExchangeRate]:
        return self._rates
