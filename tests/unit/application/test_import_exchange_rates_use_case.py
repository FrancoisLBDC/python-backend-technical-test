from datetime import UTC, datetime
from decimal import Decimal

from application.use_cases.import_exchange_rates import ImportExchangeRatesUseCase
from domain.entities import Currency, ExchangeRate
from tests.unit.application.fakes import (
    FakeEventPublisher,
    FakeExchangeRateRepository,
    FakeExchangeRateSource,
)

_AS_OF = datetime(2026, 9, 7, 16, 0, tzinfo=UTC)


class TestImportExchangeRatesUseCase:
    def test_saves_every_fetched_rate(self):
        rates = [
            ExchangeRate(currency=Currency("USD"), versus_euro_rate=Decimal("1.1"), as_of=_AS_OF),
            ExchangeRate(currency=Currency("GBP"), versus_euro_rate=Decimal("0.85"), as_of=_AS_OF),
        ]
        source = FakeExchangeRateSource(rates)
        repository = FakeExchangeRateRepository()
        use_case = ImportExchangeRatesUseCase(source, repository, FakeEventPublisher())

        summary = use_case.execute()

        assert repository.saved == rates
        assert summary.imported_count == 2

    def test_returns_zero_count_when_source_has_no_rates(self):
        source = FakeExchangeRateSource([])
        repository = FakeExchangeRateRepository()
        use_case = ImportExchangeRatesUseCase(source, repository, FakeEventPublisher())

        summary = use_case.execute()

        assert summary.imported_count == 0
        assert repository.saved == []

    def test_publishes_an_event_with_no_previous_rate_for_a_brand_new_currency(self):
        rates = [
            ExchangeRate(currency=Currency("USD"), versus_euro_rate=Decimal("1.1"), as_of=_AS_OF),
        ]
        source = FakeExchangeRateSource(rates)
        repository = FakeExchangeRateRepository()
        event_publisher = FakeEventPublisher()
        use_case = ImportExchangeRatesUseCase(source, repository, event_publisher)

        use_case.execute()

        assert len(event_publisher.published) == 1
        event = event_publisher.published[0]
        assert event.currency == Currency("USD")
        assert event.previous_rate is None
        assert event.new_rate == Decimal("1.1")
        assert event.as_of == _AS_OF

    def test_publishes_an_event_with_the_previous_rate_when_a_currency_changes(self):
        existing = ExchangeRate(
            currency=Currency("USD"), versus_euro_rate=Decimal("1.05"), as_of=_AS_OF
        )
        repository = FakeExchangeRateRepository({"USD": existing})
        new_rates = [
            ExchangeRate(currency=Currency("USD"), versus_euro_rate=Decimal("1.1"), as_of=_AS_OF),
        ]
        source = FakeExchangeRateSource(new_rates)
        event_publisher = FakeEventPublisher()
        use_case = ImportExchangeRatesUseCase(source, repository, event_publisher)

        use_case.execute()

        assert len(event_publisher.published) == 1
        event = event_publisher.published[0]
        assert event.currency == Currency("USD")
        assert event.previous_rate == Decimal("1.05")
        assert event.new_rate == Decimal("1.1")

    def test_publishes_no_event_when_a_currency_is_reimported_unchanged(self):
        existing = ExchangeRate(
            currency=Currency("USD"), versus_euro_rate=Decimal("1.1"), as_of=_AS_OF
        )
        repository = FakeExchangeRateRepository({"USD": existing})
        source = FakeExchangeRateSource([existing])
        event_publisher = FakeEventPublisher()
        use_case = ImportExchangeRatesUseCase(source, repository, event_publisher)

        use_case.execute()

        assert event_publisher.published == []
