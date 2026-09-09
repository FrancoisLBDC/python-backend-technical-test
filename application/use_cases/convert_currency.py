from decimal import Decimal

from application.dtos import ConversionResult
from application.ports.exchange_rate_repository import ExchangeRateRepository
from domain.conversion import convert_amount
from domain.entities import REFERENCE_CURRENCY, Currency, Money


class ConvertCurrencyUseCase:
    def __init__(self, repository: ExchangeRateRepository) -> None:
        self._repository = repository

    def execute(
        self, amount: Decimal, source_currency: Currency, target_currency: Currency
    ) -> ConversionResult:
        from_rate = self._rate_for(source_currency)
        to_rate = self._rate_for(target_currency)
        converted_amount = convert_amount(amount, from_rate, to_rate)
        return ConversionResult(
            source=Money(amount=amount, currency=source_currency),
            converted=Money(amount=converted_amount, currency=target_currency),
        )

    def _rate_for(self, currency: Currency) -> Decimal:
        if currency == REFERENCE_CURRENCY:
            return Decimal("1")
        return self._repository.get_rate(currency).versus_euro_rate
