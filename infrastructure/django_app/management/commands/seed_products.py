from decimal import Decimal

from django.core.management.base import BaseCommand

from domain.entities import REFERENCE_CURRENCY
from infrastructure.django_app.models import ProductModel

_PRODUCTS = [
    {
        "product_id": "P-001",
        "title": "Wireless Mouse",
        "price": Decimal("29.99"),
        "currency_code": "USD",
    },
    {
        "product_id": "P-002",
        "title": "Mechanical Keyboard",
        "price": Decimal("89.90"),
        "currency_code": "CHF",
    },
    {
        "product_id": "P-003",
        "title": "Noise Cancelling Headphones",
        "price": Decimal("199.00"),
        "currency_code": "GBP",
    },
    {
        "product_id": "P-004",
        "title": "4K Monitor",
        "price": Decimal("45000"),
        "currency_code": "JPY",
    },
    {
        "product_id": "P-005",
        "title": "USB-C Hub",
        "price": Decimal("39.50"),
        "currency_code": "EUR",
    },
]


class Command(BaseCommand):
    help = "Seed a fixed list of fake products used to demo the exchange-rate-change event."

    def handle(self, *args, **options):
        created_count = 0
        for data in _PRODUCTS:
            is_reference_currency = data["currency_code"] == REFERENCE_CURRENCY.code
            _, created = ProductModel.objects.get_or_create(
                product_id=data["product_id"],
                defaults={
                    "title": data["title"],
                    "price": data["price"],
                    "currency_code": data["currency_code"],
                    "converted_price": data["price"] if is_reference_currency else None,
                },
            )
            if created:
                created_count += 1
        self.stdout.write(
            self.style.SUCCESS(f"Seeded {created_count} new product(s) ({len(_PRODUCTS)} total).")
        )
