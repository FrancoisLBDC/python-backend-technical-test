from datetime import UTC, datetime

from application.dtos import ImportSummary
from application.ports.exchange_rate_repository import ExchangeRateRepository
from application.ports.exchange_rate_source import ExchangeRateSource


class ImportExchangeRatesUseCase:
    def __init__(self, source: ExchangeRateSource, repository: ExchangeRateRepository) -> None:
        self._source = source
        self._repository = repository

    def execute(self) -> ImportSummary:
        run_at = datetime.now(UTC)
        rates = self._source.fetch_rates()
        self._repository.save_many(rates)
        return ImportSummary(imported_count=len(rates), as_of=run_at)
