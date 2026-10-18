# Project Goblin (Phase 0)

Private tool for two players. Built from Product Brief v0.4.

## What exists
- `db/schema.sql` Postgres schema (prices, sync state, users, characters, recipes, alert rules)
- `goblin/ahledger.py` API client: honors Cache-Control, ETag, Retry-After; parses the price table
- `goblin/sync.py` hourly copy of our market and the opposite faction
- `goblin/calc.py` net profit, vendor floor, inflation index, real discount, reliability rating
- `tests/` unit tests

## Run
    cp .env.example .env   # fill in, pick the market
    docker compose up -d --build
    docker compose logs -f sync
    # tests: pip install -r requirements.txt && python -m pytest

## Not yet built
AI layer, alert engine, Discord, web app, login, item/recipe catalog fetch, deposit formula.
