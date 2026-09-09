# Technical test about currency conversion API

## Purpose

This repository is a project following Clean Architecture, done with Django and PostgreSQL, PEP8 styling.  

Its purpose is to give a simplified API to convert the value of a given currency to its target currency.


## How to setup the project

Prerequisites: Docker + Docker Compose (install the desktop app or the docker engine https://docs.docker.com/get-started/)

Copy .env.example to .env

then start the project with `docker compose up -d` 


## CI commands

Tests : `docker compose exec app pytest`

Linter : `docker compose exec app ruff check .` 

Formatter : `docker compose exec app ruff format --check .`

## Usage / tasks

Import exchange rates from the ECB into the database :
```bash
docker compose exec app python manage.py import_exchange_rates
```

Try the parser specifically
```bash
docker compose exec app python manage.py shell -c "from infrastructure.parser.query_parser import QueryParser; print(QueryParser().parse('10.32 EUR to USD'))"
```

Once rates are imported, convert an amount via `GET /money/convert`:

```bash
curl "http://localhost:8000/money/convert?query=10.32%20EUR%20to%20USD"
```

```json
{"answer": "10.32 EUR = 11.30 USD"}
```

## Bonus — Event-driven architecture

Every time `import_exchange_rates` imports a rate that is new or has changed, an `ExchangeRateChanged`
event is published in-process and consumed to recompute the `converted_price` (in EUR) of every fake
product priced in that currency. A same-day re-import with unchanged values publishes nothing.

Add the fake products:
```bash
docker compose exec app python manage.py seed_products
```

This seeds a fixed list of 5 products across USD, CHF, GBP, JPY and EUR (safe to re-run, it's
idempotent). The EUR product gets its `converted_price` set immediately since EUR needs no
conversion; the others start at `NULL` until a rate import triggers a conversion.

To see it working quickly:
```bash
docker compose exec app python manage.py seed_products
docker compose exec app python manage.py import_exchange_rates
docker compose exec app python manage.py shell -c "
from infrastructure.django_app.models import ProductModel
for p in ProductModel.objects.all().order_by('product_id'):
    print(p.product_id, p.title, p.price, p.currency_code, p.converted_price)
"
```

The first import flips every non-EUR product from `converted_price = None` to a computed value
(every currency is "new" from the DB's point of view). Re-running `import_exchange_rates` right
after changes nothing, since no rate actually changed.

## Known limitations & design trade-offs

A few questions came up while building this that were deliberately decided one way rather than
silently left unconsidered — noted here rather than implemented, since they go beyond the brief.

### `converted_price` on newly created products isn't backfilled

The bonus consumer (`UpdateProductConversionsUseCase`) only recomputes `converted_price` in
reaction to an `ExchangeRateChanged` event. A product inserted (via `seed_products`, or any future
product-creation path) after the last rate change for its currency stays at
`converted_price = NULL` until the *next* change for that currency — there's no catch-up at
creation time, only push-on-change.

A natural fix would be to compute `converted_price` at insertion time by calling
`ExchangeRateRepository.get_rate()` for the product's currency — the same lookup
`ConvertCurrencyUseCase` already does for a one-off `GET /money/convert` call — so every product
would start with a coherent value instead of `NULL`. Left unimplemented on purpose: it's outside
the bonus's event-driven scope as given, and the current `NULL → value` flip on the first import
is also what makes the event's effect visible in a demo.

### `as_of` is a `datetime`, even though the only real source is date-only

`ExchangeRate.as_of` (domain), `ExchangeRateModel.as_of` (DB) and `ExchangeRateChanged.as_of`
(event) are all typed `datetime`, but the ECB feed only ever publishes a date
(`<Cube time="2026-09-09">`) — `infrastructure/ecb/parser.py` parses it and pads it to midnight
UTC. A plain `date` would be more honest about the precision the ECB adapter can actually produce
today.

`datetime` was kept anyway: it keeps `as_of` symmetric with `ExchangeRateChanged.occurred_at` (the
actual import-processing timestamp) in the event, and it means a future intraday source could
supply a real time-of-day through the same field with no change to the domain/event contracts —
only its own adapter would differ. The ECB adapter is simply the one source that always produces
`00:00:00 UTC`.

### `converted_price` stored as a plain scalar, not a currency-keyed object

At the domain level `Product.converted_price` is already a `Money` (amount + currency), so a
tempting alternative was to mirror that in the DB too — e.g. a `JSONField` keyed by currency
(`{"EUR": 11.30}`) instead of a plain `DecimalField`.

Kept the scalar column instead: the brief's table already shows `converted_price` as a single
column, the same way `price`/`currency` are two separate columns rather than one combined object;
the target currency in this app is always EUR (`REFERENCE_CURRENCY`), so a currency-keyed
structure would just store a constant key on every row, resolving no real ambiguity; and a
`DecimalField` stays trivially filterable/sortable (`WHERE converted_price > X`) where a
`JSONField` would need a cast for the simplest query. Nothing is lost at the domain boundary
either way — `Product.converted_price` is already unambiguous there, it's only the raw DB column
that's a scalar, exactly like `price` already is next to its own `currency` column.

### One simple in-process event bus — but the seam is real

`ExchangeRateChanged` is published through `EventPublisher`
(`application/ports/event_publisher.py`), a `Protocol` with a single `publish(event) -> None`
method whose docstring already allows delivery "synchronously or otherwise" — the port itself
doesn't assume any transport. The only adapter behind it today is `InProcessEventBus`
(`infrastructure/events/in_process_event_bus.py`): a plain in-memory list of subscriber
callables, fan-out happens synchronously in the same process, nothing persisted, nothing survives
a restart.

No broker (Kafka or otherwise) was set up for this bonus on purpose: the only consumer,
`UpdateProductConversionsUseCase`, is subscribed to the same bus by the same
`import_exchange_rates` command that publishes
(`infrastructure/django_app/management/commands/import_exchange_rates.py`) — there's no actual
cross-process or cross-service delivery need to justify a topic, partitions, or producer/consumer
config for this exercise. But `ImportExchangeRatesUseCase` and `UpdateProductConversionsUseCase`
only ever depend on the `EventPublisher` port and the `subscribe`/`handle` contract, never on
`InProcessEventBus` directly — so plugging in a Kafka-backed adapter (a producer calling
`publish()`, a consumer process invoking the same `handle()` on message receipt) would mean
adding one new adapter under `infrastructure/events/`, with no change to domain, application, or
the use cases themselves.

### No logging configured

`config/settings.py` has no `LOGGING` config today, so the app runs on Django's bare defaults —
nothing is visible about what it actually does (rates imported, events published, products
updated, rejected queries) beyond an unhandled 500 reaching the console.
