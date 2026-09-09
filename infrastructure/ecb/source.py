import requests

from domain.entities import ExchangeRate
from domain.exceptions import ExchangeRateSourceError
from infrastructure.ecb.parser import parse_daily_rates

DEFAULT_ECB_RATES_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"


class EcbExchangeRateSource:
    def __init__(self, url: str = DEFAULT_ECB_RATES_URL, timeout: float = 10.0) -> None:
        self._url = url
        self._timeout = timeout

    def fetch_rates(self) -> list[ExchangeRate]:
        try:
            response = requests.get(self._url, timeout=self._timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ExchangeRateSourceError(f"Failed to fetch ECB rates from {self._url}") from exc
        return parse_daily_rates(response.content)
