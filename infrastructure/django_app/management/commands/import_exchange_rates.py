from django.conf import settings
from django.core.management.base import BaseCommand

from application.use_cases.import_exchange_rates import ImportExchangeRatesUseCase
from application.use_cases.update_product_conversions import UpdateProductConversionsUseCase
from infrastructure.django_app.repositories import (
    DjangoExchangeRateRepository,
    DjangoProductRepository,
)
from infrastructure.ecb.source import EcbExchangeRateSource
from infrastructure.events.in_process_event_bus import InProcessEventBus


class Command(BaseCommand):
    help = "Import the latest exchange rates published by the European Central Bank."

    def handle(self, *args, **options):
        event_bus = InProcessEventBus()
        event_bus.subscribe(UpdateProductConversionsUseCase(DjangoProductRepository()).handle)
        use_case = ImportExchangeRatesUseCase(
            source=EcbExchangeRateSource(url=settings.ECB_RATES_URL),
            repository=DjangoExchangeRateRepository(),
            event_publisher=event_bus,
        )
        summary = use_case.execute()
        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {summary.imported_count} exchange rate(s) as of "
                f"{summary.as_of.isoformat()}"
            )
        )
