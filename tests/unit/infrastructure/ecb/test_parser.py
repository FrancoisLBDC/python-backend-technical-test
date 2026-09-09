from datetime import UTC, datetime
from decimal import Decimal

import pytest

from domain.entities import Currency, ExchangeRate
from domain.exceptions import ExchangeRateSourceError
from infrastructure.ecb.parser import parse_daily_rates

_VALID_FEED = b"""<?xml version="1.0" encoding="UTF-8"?>
<gesmes:Envelope xmlns:gesmes="http://www.gesmes.org/xml/2002-08-01"
                  xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref">
    <gesmes:subject>Reference rates</gesmes:subject>
    <Cube>
        <Cube time="2026-09-07">
            <Cube currency="USD" rate="1.1000"/>
            <Cube currency="GBP" rate="0.8500"/>
        </Cube>
    </Cube>
</gesmes:Envelope>
"""


class TestParseDailyRates:
    def test_parses_every_currency_cube_with_the_dated_as_of(self):
        rates = parse_daily_rates(_VALID_FEED)

        assert rates == [
            ExchangeRate(
                currency=Currency("USD"),
                versus_euro_rate=Decimal("1.1000"),
                as_of=datetime(2026, 9, 7, tzinfo=UTC),
            ),
            ExchangeRate(
                currency=Currency("GBP"),
                versus_euro_rate=Decimal("0.8500"),
                as_of=datetime(2026, 9, 7, tzinfo=UTC),
            ),
        ]

    def test_returns_an_empty_list_when_the_dated_cube_has_no_currencies(self):
        feed = b"""<?xml version="1.0" encoding="UTF-8"?>
        <gesmes:Envelope xmlns:gesmes="http://www.gesmes.org/xml/2002-08-01"
                          xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref">
            <Cube><Cube time="2026-09-07"/></Cube>
        </gesmes:Envelope>
        """

        assert parse_daily_rates(feed) == []

    def test_raises_when_the_xml_is_not_well_formed(self):
        with pytest.raises(ExchangeRateSourceError):
            parse_daily_rates(b"not xml")

    def test_raises_when_the_dated_cube_is_missing(self):
        feed = b"""<?xml version="1.0" encoding="UTF-8"?>
        <gesmes:Envelope xmlns:gesmes="http://www.gesmes.org/xml/2002-08-01"
                          xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref">
            <Cube/>
        </gesmes:Envelope>
        """

        with pytest.raises(ExchangeRateSourceError):
            parse_daily_rates(feed)

    def test_raises_when_a_rate_attribute_is_not_a_number(self):
        feed = b"""<?xml version="1.0" encoding="UTF-8"?>
        <gesmes:Envelope xmlns:gesmes="http://www.gesmes.org/xml/2002-08-01"
                          xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref">
            <Cube><Cube time="2026-09-07">
                <Cube currency="USD" rate="not-a-number"/>
            </Cube></Cube>
        </gesmes:Envelope>
        """

        with pytest.raises(ExchangeRateSourceError):
            parse_daily_rates(feed)

    def test_raises_when_a_currency_code_is_invalid(self):
        feed = b"""<?xml version="1.0" encoding="UTF-8"?>
        <gesmes:Envelope xmlns:gesmes="http://www.gesmes.org/xml/2002-08-01"
                          xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref">
            <Cube><Cube time="2026-09-07">
                <Cube currency="US" rate="1.1"/>
            </Cube></Cube>
        </gesmes:Envelope>
        """

        with pytest.raises(ExchangeRateSourceError):
            parse_daily_rates(feed)
