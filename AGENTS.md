# AGENTS.md

Context and working rules for any AI coding agent (or human) contributing to this repository.

## Project context

This repository is a Python Backend technical test: a simplified currency conversion
API inspired by Google's "10 dollars in euros" search feature. Given a query such as
`10.32 EUR to USD`, the system resolves the converted amount using exchange rates sourced from
the ECB daily feed (https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml).

Mandatory constraints from the test brief:

- Clean Architecture.
- Built on Django or FastAPI — this repo uses **Django**.
- Any DBMS — this repo uses **PostgreSQL**.
- PEP8 style, code must be formatted and tested.

Deliverables and their current status:

1. **Task 1 — Import CLI**: extract conversion rates from the ECB XML feed and push them to the
   DB. ✅ Done — `python manage.py import_exchange_rates`
   ([infrastructure/django_app/management/commands/import_exchange_rates.py](infrastructure/django_app/management/commands/import_exchange_rates.py)).
2. **Task 2 — Interpreter**: a lexer/parser (PLY) that parses a query like `10.32 EUR to USD` and
   converts it using rates stored in the DB, rounded to 2 decimal places. ✅ Done —
   [infrastructure/parser/](infrastructure/parser/) + [domain/conversion.py](domain/conversion.py).
3. **Task 3 — REST endpoint**: `GET /money/convert?query=10.32%20EUR%20to%20USD` returning
   `{"answer": "10.32 EUR = 11.30 USD"}`; `POST` must return `405`; a missing `query` param must
   return `400` with plain-text body `Query parameter is required`. ✅ Done —
   [infrastructure/django_app/views.py](infrastructure/django_app/views.py) (`ConvertMoneyView`),
   wired in [config/urls.py](config/urls.py).
4. **Bonus — Event-driven architecture**: every time a rate is imported or updated, emit an event
   (currency pair, new rate, previous rate if any, timestamp) consumed to update converted prices
   on a product list. ❌ Not started.

## Golden rule: stay in scope

**Any change or improvement outside the strict scope of the technical test brief must be
validated with the user before implementation.** This covers: extra endpoints or fields, unasked
refactors, new dependencies, "nice to have" abstractions, speculative extensibility, etc.

When you notice something worth doing that isn't explicitly requested, propose it and wait for a
go-ahead instead of implementing it. This is a graded exercise the candidate will walk through
live with the evaluator — unrequested scope changes are a liability, not a feature. When a task
description is ambiguous, prefer the smallest change that satisfies the brief over the most
"complete" one.

## Architecture

Strict Clean Architecture / ports-and-adapters. The dependency rule flows one way — inner layers
never import from outer layers:

```
domain/            <- innermost, zero external dependencies (not even on application/)
  entities.py         Currency, Money, ExchangeRate, REFERENCE_CURRENCY (EUR)
  conversion.py       convert_amount(): pure conversion math, ROUND_HALF_UP to 2 decimals
  exceptions.py       DomainError and subclasses (UnknownCurrency, RateNotFound, InvalidQuery,
                       ExchangeRateSourceError)

application/        <- depends only on domain/
  dtos.py             ParsedQuery, ConversionResult, ImportSummary
  ports/              Protocol interfaces the use cases need from the outside world
    exchange_rate_repository.py   ExchangeRateRepository (get_rate / save_rate / save_many)
    exchange_rate_source.py       ExchangeRateSource (fetch_rates)
  use_cases/          orchestration only, no concrete I/O
    convert_currency.py           ConvertCurrencyUseCase
    import_exchange_rates.py      ImportExchangeRatesUseCase

infrastructure/     <- depends on application/ + domain/, implements the ports
  django_app/         Django models/migrations, DjangoExchangeRateRepository, management command
  ecb/                EcbExchangeRateSource + ECB XML parser (Task 1 adapter)
  parser/             PLY lexer/grammar/QueryParser (Task 2 adapter)

config/              <- outermost: wiring only (Django settings, urls, wsgi, asgi)
```

Rules to enforce on every change:

- `domain/` never imports Django, `requests`, `ply`, or anything from `application/` /
  `infrastructure/`.
- `application/` never imports Django, `requests`, `ply`, or a concrete infrastructure class —
  only `domain/` and its own `ports/` (`typing.Protocol`, not ABCs — keep new ports duck-typed
  the same way).
- `infrastructure/*` implements `application/ports/*` and is the only place allowed to import the
  Django ORM, `requests`, `ply`.
- New I/O (DB, HTTP, external API, message broker) → a new adapter under `infrastructure/`, behind
  a `Protocol` in `application/ports/`, injected into a use case. Never reference a concrete
  infrastructure type from a use case's signature.
- Use cases stay thin: fetch through a port, run domain logic, return a DTO. Presentation
  concerns (HTTP status codes, JSON shape, error text) belong to the infrastructure/config layer
  that calls the use case (`ConvertMoneyView` for Task 3), not to the use case itself.

## Tech stack

- Python 3.12, Django 5.x, PostgreSQL 16 (`psycopg[binary]`)
- `ply` for the Task 2 lexer/parser (see gotchas below)
- `requests` for the ECB feed fetch
- pytest + pytest-django, `ruff` (lint + format), `coverage`
- Docker / docker-compose for local dev

## Commands

```bash
docker compose up -d                                              # start db + app (runs migrations via entrypoint)
docker compose exec app python manage.py import_exchange_rates    # Task 1 CLI
docker compose exec app pytest                                    # tests
docker compose exec app ruff check .                              # lint (PEP8 + import order + Django rules)
docker compose exec app ruff format --check .                     # format check
```

## Conventions and gotchas already in the codebase

- **Rounding**: always `ROUND_HALF_UP` to 2 decimal places via
  [domain/conversion.py](domain/conversion.py) `convert_amount()` — never round anywhere else.
- **Conversion math**: triangulates through EUR (`REFERENCE_CURRENCY`) as
  `amount / from_rate * to_rate`; EUR's own rate is the constant `Decimal("1")` in
  `ConvertCurrencyUseCase._rate_for`, never looked up in the repository.
- **Currency codes**: validated as 3 uppercase letters in `Currency.__post_init__`; invalid codes
  raise `UnknownCurrency` immediately at construction.
- **Domain exceptions** are named after the failure, not suffixed `Error` (e.g. `RateNotFound`,
  not `RateNotFoundError`) — `ruff` rule `N818` is deliberately disabled for
  `domain/exceptions.py`; don't add the suffix back.
- **PLY lexer/grammar** ([infrastructure/parser/lexer.py](infrastructure/parser/lexer.py),
  [grammar.py](infrastructure/parser/grammar.py)) discover rules from function docstrings at
  import time — these modules must never run under `python -OO` / `PYTHONOPTIMIZE=2`, and rule
  functions must keep their docstrings. `t_xxx` / `p_xxx` naming is required by PLY, hence `ruff`
  rule `N802` is disabled for `lexer.py`.
- **`QueryParser`** wraps the PLY singleton `lexer`/`parser` with a module-level
  `threading.Lock` ([infrastructure/parser/query_parser.py](infrastructure/parser/query_parser.py))
  because PLY keeps mutable parse state on those singletons — never bypass the lock or
  instantiate a second lexer/parser without it.
- **`ConvertMoneyView`** ([infrastructure/django_app/views.py](infrastructure/django_app/views.py))
  defines only `get()`; all error paths (`DomainError` and subclasses) return plain-text
  `HttpResponseBadRequest`, matching the single error format the test brief's curl examples show
  — don't introduce a JSON error body.
- **Django 5+ auto-adds `HEAD`** to any view that defines `get()`
  (`django.views.generic.base.View.setup()` sets `self.head = self.get`). A `POST` to a GET-only
  view therefore returns `Allow: GET, HEAD, OPTIONS`, not `Allow: GET` — this is normal, current
  Django behavior, not a bug to fix.

## Testing

- `tests/unit/` — pure domain/application/infrastructure-parser tests, no DB, no network (see
  [tests/unit/application/fakes.py](tests/unit/application/fakes.py) for the in-memory fakes used
  to test use cases against `application/ports/*`).
- `tests/integration/` — hits the real Django ORM/DB (`DjangoExchangeRateRepository`, the
  `import_exchange_rates` management command).
- `tests/e2e/` — full request/response tests against `/money/convert` via Django's `Client`
  ([tests/e2e/test_convert_endpoint.py](tests/e2e/test_convert_endpoint.py)), reproducing the
  brief's curl examples (success, `POST` → 405, missing `query` → 400).
- Coverage is scoped to `domain`, `application`, `infrastructure` (see `pyproject.toml`),
  migrations excluded.
- PEP8/style is enforced by `ruff check` + `ruff format --check`, both run in CI on every PR
  ([.github/workflows/ci.yml](.github/workflows/ci.yml)) — run them locally before considering a
  change done.

## Current state / what's next

**Keep this section up to date.** Before concluding any task that changes what's done or pending
(a task/bonus completed, a new gotcha introduced, an architectural decision made), update this
section — and any other part of this file it affects — to reflect the new state. This file is
only useful to the next agent if it matches reality; do not leave it describing a past state.

- Done: Task 1 (import CLI), Task 2 (interpreter), Task 3 (REST endpoint), CI (lint + tests on
  PR).
- Not started: the event-driven architecture bonus.
- All three mandatory tasks are complete and verified end-to-end (automated tests + a live
  `curl` session matching the brief's exact examples). Anything beyond the bonus (extra fields,
  extra routes, alternative error formats, etc.) needs validation from the user first, per the
  golden rule above.
