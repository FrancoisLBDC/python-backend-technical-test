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
