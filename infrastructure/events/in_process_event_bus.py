from collections.abc import Callable

from domain.events import ExchangeRateChanged

Handler = Callable[[ExchangeRateChanged], None]


class InProcessEventBus:
    def __init__(self) -> None:
        self._subscribers: list[Handler] = []

    def subscribe(self, handler: Handler) -> None:
        self._subscribers.append(handler)

    def publish(self, event: ExchangeRateChanged) -> None:
        for handler in self._subscribers:
            handler(event)
