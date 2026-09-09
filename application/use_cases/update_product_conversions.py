from decimal import Decimal

from application.ports.product_repository import ProductRepository
from domain.conversion import convert_amount
from domain.entities import REFERENCE_CURRENCY, Money
from domain.events import ExchangeRateChanged


class UpdateProductConversionsUseCase:
    def __init__(self, product_repository: ProductRepository) -> None:
        self._product_repository = product_repository

    def handle(self, event: ExchangeRateChanged) -> None:
        products = self._product_repository.list_by_currency(event.currency)
        for product in products:
            converted_amount = convert_amount(product.price.amount, event.new_rate, Decimal("1"))
            self._product_repository.update_converted_price(
                product.product_id, Money(amount=converted_amount, currency=REFERENCE_CURRENCY)
            )
