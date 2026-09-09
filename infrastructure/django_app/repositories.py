from collections.abc import Iterable

from django.db import transaction

from domain.entities import Currency, ExchangeRate
from domain.exceptions import RateNotFound
from infrastructure.django_app.models import ExchangeRateModel


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
