import sys
import threading
from decimal import Decimal

import pytest

from application.dtos import ParsedQuery
from domain.entities import Currency
from domain.exceptions import InvalidQuery
from infrastructure.parser.query_parser import QueryParser


@pytest.fixture
def parse():
    return QueryParser().parse


class TestQueryParser:
    def test_parses_a_simple_query(self, parse):
        result = parse("10 EUR to USD")

        assert result == ParsedQuery(
            amount=Decimal("10"), source_currency=Currency("EUR"), target_currency=Currency("USD")
        )

    def test_parses_a_decimal_amount(self, parse):
        result = parse("10.32 EUR to USD")

        assert result.amount == Decimal("10.32")

    def test_tolerates_surrounding_whitespace(self, parse):
        result = parse("  10 EUR to USD\n")

        assert result.amount == Decimal("10")

    def test_is_safe_under_concurrent_calls(self, parse):
        # A low switch interval forces frequent thread preemption, reliably
        # surfacing the race on the shared PLY lexer/parser state if the
        # QueryParser's lock were ever removed, instead of relying on luck.
        original_interval = sys.getswitchinterval()
        sys.setswitchinterval(1e-6)
        try:
            errors = []

            def worker(amount: int) -> None:
                text = f"{amount} EUR to USD"
                for _ in range(50):
                    try:
                        result = parse(text)
                    except Exception as exc:  # noqa: BLE001 -- any failure is a bug here
                        errors.append((amount, exc))
                    else:
                        if result.amount != Decimal(amount):
                            errors.append((amount, result.amount))

            threads = [threading.Thread(target=worker, args=(n,)) for n in range(1, 9)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
        finally:
            sys.setswitchinterval(original_interval)

        assert errors == []

    @pytest.mark.parametrize(
        "text",
        [
            "",
            "   ",
            "10 EUR",
            "10 EUR USD",
            "EUR to USD",
            "10 to USD",
            "10 EUR to",
            "ten EUR to USD",
            "10 EU to USD",
            "10 EUR to USD extra",
            "10 EUR2 to USD",
            "Converting 10 EUR to USD",
            "10 eur to usd",
            "10 EUR TO USD",
        ],
    )
    def test_rejects_malformed_queries(self, parse, text):
        with pytest.raises(InvalidQuery):
            parse(text)
