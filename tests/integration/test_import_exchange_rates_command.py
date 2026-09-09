from datetime import UTC, datetime
from decimal import Decimal
from io import StringIO
from unittest.mock import Mock, patch

import pytest
from django.core.management import call_command

from infrastructure.django_app.models import ExchangeRateModel, ProductModel

pytestmark = pytest.mark.django_db

_FEED = b"""<?xml version="1.0" encoding="UTF-8"?>
<gesmes:Envelope xmlns:gesmes="http://www.gesmes.org/xml/2002-08-01"
                  xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref">
    <Cube><Cube time="2026-09-07">
        <Cube currency="USD" rate="1.1000"/>
        <Cube currency="GBP" rate="0.8500"/>
    </Cube></Cube>
</gesmes:Envelope>
"""


class TestImportExchangeRatesCommand:
    def test_persists_every_rate_from_the_ecb_feed(self):
        response = Mock(content=_FEED)
        response.raise_for_status = Mock()

        with patch("requests.get", return_value=response):
            call_command("import_exchange_rates", stdout=StringIO())

        saved = {model.currency_code: model.rate for model in ExchangeRateModel.objects.all()}
        assert saved == {"USD": Decimal("1.1000"), "GBP": Decimal("0.8500")}

    def test_prints_a_summary_of_the_import(self):
        response = Mock(content=_FEED)
        response.raise_for_status = Mock()
        out = StringIO()

        with patch("requests.get", return_value=response):
            call_command("import_exchange_rates", stdout=out)

        assert "Imported 2 exchange rate(s)" in out.getvalue()

    def test_updates_converted_price_of_products_whose_currency_rate_changed(self):
        ExchangeRateModel.objects.create(
            currency_code="USD", rate=Decimal("1.0500"), as_of=datetime(2026, 9, 6, tzinfo=UTC)
        )
        ProductModel.objects.create(
            product_id="P-1", title="Widget", price=Decimal("110.00"), currency_code="USD"
        )
        response = Mock(content=_FEED)
        response.raise_for_status = Mock()

        with patch("requests.get", return_value=response):
            call_command("import_exchange_rates", stdout=StringIO())

        product = ProductModel.objects.get(product_id="P-1")
        assert product.converted_price == Decimal("100.00")

    def test_does_not_touch_products_when_the_rate_is_reimported_unchanged(self):
        ExchangeRateModel.objects.create(
            currency_code="USD", rate=Decimal("1.1000"), as_of=datetime(2026, 9, 6, tzinfo=UTC)
        )
        ProductModel.objects.create(
            product_id="P-1", title="Widget", price=Decimal("110.00"), currency_code="USD"
        )
        response = Mock(content=_FEED)
        response.raise_for_status = Mock()

        with patch("requests.get", return_value=response):
            call_command("import_exchange_rates", stdout=StringIO())

        product = ProductModel.objects.get(product_id="P-1")
        assert product.converted_price is None
