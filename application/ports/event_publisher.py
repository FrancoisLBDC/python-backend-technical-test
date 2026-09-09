from typing import Protocol

from domain.events import ExchangeRateChanged


class EventPublisher(Protocol):
    def publish(self, event: ExchangeRateChanged) -> None:
        """Deliver `event` to every subscriber, synchronously or otherwise."""
        ...
