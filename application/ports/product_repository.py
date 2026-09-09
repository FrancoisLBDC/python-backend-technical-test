from typing import Protocol

from domain.entities import Currency, Money, Product


class ProductRepository(Protocol):
    def list_by_currency(self, currency: Currency) -> list[Product]:
        """Return every product priced in `currency`."""
        ...

    def update_converted_price(self, product_id: str, converted_price: Money) -> None:
        """Persist the recomputed converted price for `product_id`."""
        ...
