from decimal import Decimal

import pytest

from domain.conversion import convert_amount

EUR = Decimal("1")


class TestConvertAmount:
    def test_identity_conversion_returns_same_amount(self):
        assert convert_amount(Decimal("10"), EUR, EUR) == Decimal("10.00")

    def test_eur_to_foreign_currency(self):
        assert convert_amount(Decimal("10"), EUR, Decimal("1.1")) == Decimal("11.00")

    def test_foreign_currency_to_eur(self):
        assert convert_amount(Decimal("11"), Decimal("1.1"), EUR) == Decimal("10.00")

    def test_cross_rate_between_two_foreign_currencies(self):
        # 10 USD -> EUR -> GBP, USD rate 1.1, GBP rate 0.85
        result = convert_amount(Decimal("10"), Decimal("1.1"), Decimal("0.85"))
        assert result == Decimal("7.73")

    @pytest.mark.parametrize(
        ("amount", "from_rate", "to_rate", "expected"),
        [
            (Decimal("10"), Decimal("1"), Decimal("1.0005"), Decimal("10.01")),
            (Decimal("10"), Decimal("1"), Decimal("1.0004"), Decimal("10.00")),
        ],
    )
    def test_rounds_half_up_to_two_decimals(self, amount, from_rate, to_rate, expected):
        assert convert_amount(amount, from_rate, to_rate) == expected
