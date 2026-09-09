from decimal import Decimal

import pytest

from domain.entities import REFERENCE_CURRENCY, Currency, Money
from infrastructure.django_app.models import ProductModel
from infrastructure.django_app.repositories import DjangoProductRepository

pytestmark = pytest.mark.django_db


class TestDjangoProductRepository:
    def test_list_by_currency_returns_only_matching_products(self):
        ProductModel.objects.create(
            product_id="P-1", title="Widget", price=Decimal("10.00"), currency_code="USD"
        )
        ProductModel.objects.create(
            product_id="P-2", title="Gadget", price=Decimal("20.00"), currency_code="GBP"
        )
        repository = DjangoProductRepository()

        products = repository.list_by_currency(Currency("USD"))

        assert [product.product_id for product in products] == ["P-1"]
        assert products[0].price == Money(Decimal("10.00"), Currency("USD"))
        assert products[0].converted_price is None

    def test_list_by_currency_maps_a_stored_converted_price(self):
        ProductModel.objects.create(
            product_id="P-1",
            title="Widget",
            price=Decimal("10.00"),
            currency_code="USD",
            converted_price=Decimal("9.09"),
        )
        repository = DjangoProductRepository()

        products = repository.list_by_currency(Currency("USD"))

        assert products[0].converted_price == Money(Decimal("9.09"), REFERENCE_CURRENCY)

    def test_update_converted_price_persists_the_value(self):
        ProductModel.objects.create(
            product_id="P-1", title="Widget", price=Decimal("10.00"), currency_code="USD"
        )
        repository = DjangoProductRepository()

        repository.update_converted_price("P-1", Money(Decimal("9.09"), REFERENCE_CURRENCY))

        model = ProductModel.objects.get(product_id="P-1")
        assert model.converted_price == Decimal("9.09")
