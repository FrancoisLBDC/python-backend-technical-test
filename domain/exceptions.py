class DomainError(Exception):
    """Base class for all domain-level errors."""


class UnknownCurrency(DomainError):
    """Raised when a currency code is not a valid ISO-4217-shaped code."""


class RateNotFound(DomainError):
    """Raised when no exchange rate is available for an otherwise valid currency."""


class InvalidQuery(DomainError):
    """Raised when a conversion query string cannot be parsed."""
