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
