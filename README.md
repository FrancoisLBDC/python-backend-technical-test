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
