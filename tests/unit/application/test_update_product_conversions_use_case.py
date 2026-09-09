from datetime import UTC, datetime
from decimal import Decimal

from application.use_cases.update_product_conversions import UpdateProductConversionsUseCase
from domain.entities import REFERENCE_CURRENCY, Currency, Money, Product
from domain.events import ExchangeRateChanged
from tests.unit.application.fakes import FakeProductRepository

_AS_OF = datetime(2026, 9, 7, 16, 0, tzinfo=UTC)


class TestUpdateProductConversionsUseCase:
    def test_recomputes_converted_price_for_products_in_the_changed_currency(self):
        product = Product(
            product_id="P-1", title="Widget", price=Money(Decimal("110.00"), Currency("USD"))
        )
        repository = FakeProductRepository([product])
        use_case = UpdateProductConversionsUseCase(repository)
        event = ExchangeRateChanged(
            currency=Currency("USD"),
            previous_rate=Decimal("1.05"),
            new_rate=Decimal("1.1"),
            as_of=_AS_OF,
            occurred_at=_AS_OF,
        )

        use_case.handle(event)

        assert repository.updated == [("P-1", Money(Decimal("100.00"), REFERENCE_CURRENCY))]

    def test_leaves_products_in_other_currencies_untouched(self):
        product = Product(
            product_id="P-2", title="Gadget", price=Money(Decimal("50.00"), Currency("GBP"))
        )
        repository = FakeProductRepository([product])
        use_case = UpdateProductConversionsUseCase(repository)
        event = ExchangeRateChanged(
            currency=Currency("USD"),
            previous_rate=None,
            new_rate=Decimal("1.1"),
            as_of=_AS_OF,
            occurred_at=_AS_OF,
        )

        use_case.handle(event)

        assert repository.updated == []

    def test_is_a_noop_when_no_product_matches_the_currency(self):
        repository = FakeProductRepository([])
        use_case = UpdateProductConversionsUseCase(repository)
        event = ExchangeRateChanged(
            currency=Currency("JPY"),
            previous_rate=None,
            new_rate=Decimal("160.0"),
            as_of=_AS_OF,
            occurred_at=_AS_OF,
        )

        use_case.handle(event)

        assert repository.updated == []
