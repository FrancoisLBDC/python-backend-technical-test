from datetime import UTC, datetime
from decimal import Decimal

import pytest

from domain.entities import Currency, ExchangeRate, Money
from domain.exceptions import UnknownCurrency


class TestCurrency:
    def test_normalizes_lowercase_code_to_uppercase(self):
        assert Currency("eur").code == "EUR"

    def test_accepts_valid_uppercase_code(self):
        assert Currency("USD").code == "USD"

    @pytest.mark.parametrize("code", ["EU", "EURO", "12A", "", "E U"])
    def test_rejects_malformed_code(self, code):
        with pytest.raises(UnknownCurrency):
            Currency(code)

    def test_is_frozen(self):
        currency = Currency("EUR")
        with pytest.raises(AttributeError):
            currency.code = "USD"

    def test_equality_is_by_value(self):
        assert Currency("EUR") == Currency("eur")


class TestExchangeRate:
    def test_holds_currency_rate_and_timestamp(self):
        as_of = datetime(2026, 9, 7, 16, 0, tzinfo=UTC)
        rate = ExchangeRate(currency=Currency("USD"), versus_euro_rate=Decimal("1.1"), as_of=as_of)
        assert rate.currency == Currency("USD")
        assert rate.versus_euro_rate == Decimal("1.1")
        assert rate.as_of == as_of


class TestMoney:
    def test_holds_amount_and_currency(self):
        money = Money(amount=Decimal("10.32"), currency=Currency("EUR"))
        assert money.amount == Decimal("10.32")
        assert money.currency == Currency("EUR")
