from datetime import UTC, datetime
from decimal import Decimal

from application.dtos import ImportSummary
from application.ports.event_publisher import EventPublisher
from application.ports.exchange_rate_repository import ExchangeRateRepository
from application.ports.exchange_rate_source import ExchangeRateSource
from domain.entities import ExchangeRate
from domain.events import ExchangeRateChanged
from domain.exceptions import RateNotFound


class ImportExchangeRatesUseCase:
    def __init__(
        self,
        source: ExchangeRateSource,
        repository: ExchangeRateRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._source = source
        self._repository = repository
        self._event_publisher = event_publisher

    def execute(self) -> ImportSummary:
        run_at = datetime.now(UTC)
        rates = self._source.fetch_rates()

        previous_rates = {rate.currency.code: self._previous_rate(rate) for rate in rates}

        self._repository.save_many(rates)

        for rate in rates:
            previous_rate = previous_rates[rate.currency.code]
            if previous_rate != rate.versus_euro_rate:
                self._event_publisher.publish(
                    ExchangeRateChanged(
                        currency=rate.currency,
                        previous_rate=previous_rate,
                        new_rate=rate.versus_euro_rate,
                        as_of=rate.as_of,
                        occurred_at=run_at,
                    )
                )

        return ImportSummary(imported_count=len(rates), as_of=run_at)

    def _previous_rate(self, rate: ExchangeRate) -> Decimal | None:
        try:
            return self._repository.get_rate(rate.currency).versus_euro_rate
        except RateNotFound:
            return None
