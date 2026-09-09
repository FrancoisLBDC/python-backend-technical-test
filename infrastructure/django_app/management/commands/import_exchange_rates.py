from django.conf import settings
from django.core.management.base import BaseCommand

from application.use_cases.import_exchange_rates import ImportExchangeRatesUseCase
from infrastructure.django_app.repositories import DjangoExchangeRateRepository
from infrastructure.ecb.source import EcbExchangeRateSource


class Command(BaseCommand):
    help = "Import the latest exchange rates published by the European Central Bank."

    def handle(self, *args, **options):
        use_case = ImportExchangeRatesUseCase(
            source=EcbExchangeRateSource(url=settings.ECB_RATES_URL),
            repository=DjangoExchangeRateRepository(),
        )
        summary = use_case.execute()
        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {summary.imported_count} exchange rate(s) as of "
                f"{summary.as_of.isoformat()}"
            )
        )
