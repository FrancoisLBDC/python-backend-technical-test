from collections.abc import Iterable

from django.db import transaction

from domain.entities import REFERENCE_CURRENCY, Currency, ExchangeRate, Money, Product
from domain.exceptions import RateNotFound
from infrastructure.django_app.models import ExchangeRateModel, ProductModel


class DjangoExchangeRateRepository:
    def get_rate(self, currency: Currency) -> ExchangeRate:
        model = (
            ExchangeRateModel.objects.filter(currency_code=currency.code).order_by("-as_of").first()
        )
        if model is None:
            raise RateNotFound(f"No rate found for {currency.code}")
        return self._to_domain(model)

    def save_rate(self, rate: ExchangeRate) -> None:
        ExchangeRateModel.objects.update_or_create(
            currency_code=rate.currency.code,
            as_of=rate.as_of,
            defaults={"rate": rate.versus_euro_rate},
        )

    def save_many(self, rates: Iterable[ExchangeRate]) -> None:
        with transaction.atomic():
            for rate in rates:
                self.save_rate(rate)

    @staticmethod
    def _to_domain(model: ExchangeRateModel) -> ExchangeRate:
        return ExchangeRate(
            currency=Currency(model.currency_code),
            versus_euro_rate=model.rate,
            as_of=model.as_of,
        )


class DjangoProductRepository:
    def list_by_currency(self, currency: Currency) -> list[Product]:
        models = ProductModel.objects.filter(currency_code=currency.code)
        return [self._to_domain(model) for model in models]

    def update_converted_price(self, product_id: str, converted_price: Money) -> None:
        ProductModel.objects.filter(product_id=product_id).update(
            converted_price=converted_price.amount
        )

    @staticmethod
    def _to_domain(model: ProductModel) -> Product:
        converted_price = None
        if model.converted_price is not None:
            converted_price = Money(amount=model.converted_price, currency=REFERENCE_CURRENCY)
        return Product(
            product_id=model.product_id,
            title=model.title,
            price=Money(amount=model.price, currency=Currency(model.currency_code)),
            converted_price=converted_price,
        )
