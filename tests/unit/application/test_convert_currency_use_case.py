from datetime import UTC, datetime
from decimal import Decimal

import pytest

from application.use_cases.convert_currency import ConvertCurrencyUseCase
from domain.entities import Currency, ExchangeRate, Money
from domain.exceptions import RateNotFound
from tests.unit.application.fakes import FakeExchangeRateRepository

_AS_OF = datetime(2026, 9, 7, 16, 0, tzinfo=UTC)


def _repo_with(**rates_by_code: Decimal) -> FakeExchangeRateRepository:
    rates = {
        code: ExchangeRate(currency=Currency(code), versus_euro_rate=rate, as_of=_AS_OF)
        for code, rate in rates_by_code.items()
    }
    return FakeExchangeRateRepository(rates)


class TestConvertCurrencyUseCase:
    def test_converts_between_two_foreign_currencies(self):
        repository = _repo_with(USD=Decimal("1.1"), GBP=Decimal("0.85"))
        use_case = ConvertCurrencyUseCase(repository)

        result = use_case.execute(Decimal("10"), Currency("USD"), Currency("GBP"))

        assert result.source == Money(Decimal("10"), Currency("USD"))
        assert result.converted == Money(Decimal("7.73"), Currency("GBP"))

    def test_converts_eur_to_foreign_currency(self):
        repository = _repo_with(USD=Decimal("1.1"))
        use_case = ConvertCurrencyUseCase(repository)

        result = use_case.execute(Decimal("10"), Currency("EUR"), Currency("USD"))

        assert result.converted == Money(Decimal("11.00"), Currency("USD"))

    def test_converts_foreign_currency_to_eur(self):
        repository = _repo_with(USD=Decimal("1.1"))
        use_case = ConvertCurrencyUseCase(repository)

        result = use_case.execute(Decimal("11"), Currency("USD"), Currency("EUR"))

        assert result.converted == Money(Decimal("10.00"), Currency("EUR"))

    def test_eur_to_eur_never_queries_the_repository(self):
        repository = _repo_with()  # empty: would raise RateNotFound if queried
        use_case = ConvertCurrencyUseCase(repository)

        result = use_case.execute(Decimal("10"), Currency("EUR"), Currency("EUR"))

        assert result.converted == Money(Decimal("10.00"), Currency("EUR"))

    def test_raises_rate_not_found_for_a_currency_never_imported(self):
        repository = _repo_with()
        use_case = ConvertCurrencyUseCase(repository)

        with pytest.raises(RateNotFound):
            use_case.execute(Decimal("10"), Currency("USD"), Currency("EUR"))
