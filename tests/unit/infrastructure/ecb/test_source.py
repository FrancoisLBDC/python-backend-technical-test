from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
import requests

from domain.entities import Currency, ExchangeRate
from domain.exceptions import ExchangeRateSourceError
from infrastructure.ecb.source import EcbExchangeRateSource

_FEED = b"""<?xml version="1.0" encoding="UTF-8"?>
<gesmes:Envelope xmlns:gesmes="http://www.gesmes.org/xml/2002-08-01"
                  xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref">
    <Cube><Cube time="2026-09-07">
        <Cube currency="USD" rate="1.1000"/>
    </Cube></Cube>
</gesmes:Envelope>
"""


class TestEcbExchangeRateSource:
    def test_fetch_rates_parses_the_response_body(self):
        response = Mock(content=_FEED)
        response.raise_for_status = Mock()
        source = EcbExchangeRateSource(url="https://example.test/rates.xml")

        with patch("requests.get", return_value=response) as get:
            rates = source.fetch_rates()

        get.assert_called_once_with("https://example.test/rates.xml", timeout=10.0)
        assert rates == [
            ExchangeRate(
                currency=Currency("USD"),
                versus_euro_rate=Decimal("1.1000"),
                as_of=datetime(2026, 9, 7, tzinfo=UTC),
            )
        ]

    def test_fetch_rates_raises_when_the_request_fails(self):
        source = EcbExchangeRateSource(url="https://example.test/rates.xml")

        with (
            patch("requests.get", side_effect=requests.ConnectionError("boom")),
            pytest.raises(ExchangeRateSourceError),
        ):
            source.fetch_rates()

    def test_fetch_rates_raises_when_the_response_is_an_http_error(self):
        response = Mock()
        response.raise_for_status = Mock(side_effect=requests.HTTPError("500"))
        source = EcbExchangeRateSource(url="https://example.test/rates.xml")

        with patch("requests.get", return_value=response), pytest.raises(ExchangeRateSourceError):
            source.fetch_rates()
