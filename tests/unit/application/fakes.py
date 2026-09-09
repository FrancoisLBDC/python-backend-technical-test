from collections.abc import Iterable
from dataclasses import replace

from domain.entities import Currency, ExchangeRate, Money, Product
from domain.events import ExchangeRateChanged
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


class FakeEventPublisher:
    def __init__(self) -> None:
        self.published: list[ExchangeRateChanged] = []

    def publish(self, event: ExchangeRateChanged) -> None:
        self.published.append(event)


class FakeProductRepository:
    def __init__(self, products: list[Product] | None = None) -> None:
        self._products: dict[str, Product] = {
            product.product_id: product for product in products or []
        }
        self.updated: list[tuple[str, Money]] = []

    def list_by_currency(self, currency: Currency) -> list[Product]:
        return [
            product for product in self._products.values() if product.price.currency == currency
        ]

    def update_converted_price(self, product_id: str, converted_price: Money) -> None:
        self._products[product_id] = replace(
            self._products[product_id], converted_price=converted_price
        )
        self.updated.append((product_id, converted_price))
