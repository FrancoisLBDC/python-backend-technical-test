from datetime import UTC, datetime
from decimal import Decimal
from urllib.parse import quote

import pytest
from django.test import Client

from domain.entities import Currency, ExchangeRate
from infrastructure.django_app.repositories import DjangoExchangeRateRepository

pytestmark = pytest.mark.django_db

_AS_OF = datetime(2026, 9, 7, 16, 0, tzinfo=UTC)


@pytest.fixture
def seed_rates():
    repository = DjangoExchangeRateRepository()
    repository.save_many(
        [
            ExchangeRate(
                currency=Currency("USD"), versus_euro_rate=Decimal("1.0950"), as_of=_AS_OF
            ),
            ExchangeRate(
                currency=Currency("CHF"), versus_euro_rate=Decimal("0.9500"), as_of=_AS_OF
            ),
        ]
    )


class TestConvertEndpoint:
    def test_get_with_a_valid_query_returns_the_converted_amount(self, seed_rates):
        client = Client()

        response = client.get(f"/money/convert?query={quote('10.32 EUR to USD')}")

        assert response.status_code == 200
        assert response["Content-Type"] == "application/json"
        assert response.json() == {"answer": "10.32 EUR = 11.30 USD"}

    def test_post_is_not_allowed(self, seed_rates):
        client = Client()

        response = client.post(f"/money/convert?query={quote('10.32 EUR to USD')}")

        assert response.status_code == 405
        # Django 5+ auto-supports HEAD whenever a view defines GET
        # (django.views.generic.base.View.setup() sets self.head = self.get),
        # so a GET-only view's Allow header is "GET, HEAD, OPTIONS", not "GET".
        assert response["Allow"] == "GET, HEAD, OPTIONS"
        assert response["Content-Type"] == "text/html; charset=utf-8"
        assert response.content == b""

    def test_get_without_query_param_returns_400(self):
        client = Client()

        response = client.get("/money/convert")

        assert response.status_code == 400
        assert response["Content-Type"] == "text/html; charset=utf-8"
        assert response.content == b"Query parameter is required"

    def test_get_with_an_invalid_query_returns_400(self):
        client = Client()

        response = client.get(f"/money/convert?query={quote('not a query')}")

        assert response.status_code == 400
        assert response["Content-Type"] == "text/html; charset=utf-8"

    def test_get_with_an_unimported_currency_returns_400(self):
        client = Client()

        response = client.get(f"/money/convert?query={quote('10 EUR to GBP')}")

        assert response.status_code == 400
        assert response["Content-Type"] == "text/html; charset=utf-8"
