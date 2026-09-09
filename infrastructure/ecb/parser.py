import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

from domain.entities import Currency, ExchangeRate
from domain.exceptions import ExchangeRateSourceError, UnknownCurrency

_NAMESPACE = {"ecb": "http://www.ecb.int/vocabulary/2002-08-01/eurofxref"}


def parse_daily_rates(content: bytes) -> list[ExchangeRate]:
    """Parse the ECB `eurofxref-daily.xml` feed into a list of ExchangeRate.

    Raises ExchangeRateSourceError if `content` does not match the expected
    feed shape (missing dated cube, missing/invalid currency or rate attributes).
    """
    try:
        root = ET.fromstring(content)
        day_cube = root.find(".//ecb:Cube[@time]", _NAMESPACE)
        if day_cube is None:
            raise ExchangeRateSourceError("ECB feed did not contain a dated rate cube")
        as_of = datetime.strptime(day_cube.attrib["time"], "%Y-%m-%d").replace(tzinfo=UTC)
        return [
            ExchangeRate(
                currency=Currency(cube.attrib["currency"]),
                versus_euro_rate=Decimal(cube.attrib["rate"]),
                as_of=as_of,
            )
            for cube in day_cube.findall("ecb:Cube", _NAMESPACE)
        ]
    except ExchangeRateSourceError:
        raise
    except (ET.ParseError, KeyError, ValueError, InvalidOperation, UnknownCurrency) as exc:
        raise ExchangeRateSourceError(f"ECB feed could not be parsed: {exc}") from exc
