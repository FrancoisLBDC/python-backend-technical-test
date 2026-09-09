from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest

from domain.entities import Currency, ExchangeRate
from domain.exceptions import RateNotFound
from infrastructure.django_app.repositories import DjangoExchangeRateRepository

pytestmark = pytest.mark.django_db

_T0 = datetime(2026, 9, 7, 16, 0, tzinfo=UTC)
_T1 = _T0 + timedelta(days=1)


class TestDjangoExchangeRateRepository:
    def test_get_rate_raises_when_currency_was_never_imported(self):
        repository = DjangoExchangeRateRepository()

        with pytest.raises(RateNotFound):
            repository.get_rate(Currency("USD"))

    def test_save_rate_then_get_rate_round_trips_through_the_domain_type(self):
        repository = DjangoExchangeRateRepository()
        rate = ExchangeRate(currency=Currency("USD"), versus_euro_rate=Decimal("1.1"), as_of=_T0)

        repository.save_rate(rate)

        assert repository.get_rate(Currency("USD")) == rate

    def test_get_rate_returns_the_most_recent_observation(self):
        repository = DjangoExchangeRateRepository()
        older = ExchangeRate(currency=Currency("USD"), versus_euro_rate=Decimal("1.1"), as_of=_T0)
        newer = ExchangeRate(currency=Currency("USD"), versus_euro_rate=Decimal("1.2"), as_of=_T1)
        repository.save_rate(older)
        repository.save_rate(newer)

        assert repository.get_rate(Currency("USD")) == newer

    def test_save_rate_upserts_on_currency_and_as_of(self):
        repository = DjangoExchangeRateRepository()
        first = ExchangeRate(currency=Currency("USD"), versus_euro_rate=Decimal("1.1"), as_of=_T0)
        corrected = ExchangeRate(
            currency=Currency("USD"), versus_euro_rate=Decimal("1.15"), as_of=_T0
        )
        repository.save_rate(first)

        repository.save_rate(corrected)

        assert repository.get_rate(Currency("USD")) == corrected

    def test_save_many_persists_every_rate(self):
        repository = DjangoExchangeRateRepository()
        rates = [
            ExchangeRate(currency=Currency("USD"), versus_euro_rate=Decimal("1.1"), as_of=_T0),
            ExchangeRate(currency=Currency("GBP"), versus_euro_rate=Decimal("0.85"), as_of=_T0),
        ]

        repository.save_many(rates)

        assert repository.get_rate(Currency("USD")) == rates[0]
        assert repository.get_rate(Currency("GBP")) == rates[1]

    def test_save_many_rolls_back_everything_when_one_rate_fails_to_save(self):
        repository = DjangoExchangeRateRepository()
        rates = [
            ExchangeRate(currency=Currency("USD"), versus_euro_rate=Decimal("1.1"), as_of=_T0),
            ExchangeRate(currency=Currency("GBP"), versus_euro_rate=Decimal("0.85"), as_of=_T0),
        ]

        original_save_rate = repository.save_rate

        def flaky_save_rate(rate):
            if rate.currency.code == "GBP":
                raise RuntimeError("boom")
            return original_save_rate(rate)

        with (
            patch.object(repository, "save_rate", side_effect=flaky_save_rate),
            pytest.raises(RuntimeError),
        ):
            repository.save_many(rates)

        with pytest.raises(RateNotFound):
            repository.get_rate(Currency("USD"))
