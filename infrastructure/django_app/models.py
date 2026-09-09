from django.db import models


class ExchangeRateModel(models.Model):
    currency_code = models.CharField(max_length=3)
    rate = models.DecimalField(max_digits=18, decimal_places=6)
    as_of = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["currency_code", "as_of"], name="unique_currency_code_as_of"
            )
        ]

    def __str__(self) -> str:
        return f"{self.currency_code} {self.rate} @ {self.as_of.isoformat()}"


class ProductModel(models.Model):
    product_id = models.CharField(max_length=64, primary_key=True)
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency_code = models.CharField(max_length=3)
    converted_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.product_id} {self.title} {self.price} {self.currency_code}"
