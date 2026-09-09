from datetime import UTC, datetime
from decimal import Decimal

from application.use_cases.import_exchange_rates import ImportExchangeRatesUseCase
from domain.entities import Currency, ExchangeRate
from tests.unit.application.fakes import FakeExchangeRateRepository, FakeExchangeRateSource

_AS_OF = datetime(2026, 9, 7, 16, 0, tzinfo=UTC)


class TestImportExchangeRatesUseCase:
    def test_saves_every_fetched_rate(self):
        rates = [
            ExchangeRate(currency=Currency("USD"), versus_euro_rate=Decimal("1.1"), as_of=_AS_OF),
            ExchangeRate(currency=Currency("GBP"), versus_euro_rate=Decimal("0.85"), as_of=_AS_OF),
        ]
        source = FakeExchangeRateSource(rates)
        repository = FakeExchangeRateRepository()
        use_case = ImportExchangeRatesUseCase(source, repository)

        summary = use_case.execute()

        assert repository.saved == rates
        assert summary.imported_count == 2

    def test_returns_zero_count_when_source_has_no_rates(self):
        source = FakeExchangeRateSource([])
        repository = FakeExchangeRateRepository()
        use_case = ImportExchangeRatesUseCase(source, repository)

        summary = use_case.execute()

        assert summary.imported_count == 0
        assert repository.saved == []
