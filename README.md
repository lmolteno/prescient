# Prescient

A space-weather data service. It ingests two public feeds and serves the
results over an HTTP API:

- **NOAA SWPC** — daily solar (sunspot) region observations and solar events
  (flares, X-ray events, radio bursts).
- **Stanford SDO/HMI** — continuum images of the Sun, from which sunspot
  umbra/penumbra contours are extracted with OpenCV and normalized to the
  solar disk.

This is a Python port of the original Kotlin/Ktor service, rebuilt on FastAPI,
SQLAlchemy 2.0 (async), Alembic, and Pydantic v2.

## Architecture

Two independent processes share one Postgres database:

| Process | Command | Role |
|---|---|---|
| **API** | `prescient-api` | Read-only HTTP API (FastAPI + Uvicorn). Stateless; scale freely. |
| **Poller** | `prescient-poller` | Runs the SWPC + HMI ingest jobs. Run exactly one. |

Splitting ingestion from serving means the API can be scaled to multiple
replicas without duplicating fetches or fighting over inserts.

```
src/prescient/
├── config.py            # env-based settings (pydantic-settings)
├── db.py                # async engine / session factory
├── models.py            # SQLAlchemy ORM tables
├── api/                 # FastAPI app, routes, dependencies
├── poller/              # background ingest jobs + entrypoint
└── sources/
    ├── swpc/            # NOAA client, region/event parsing, repository
    └── sdo/             # JSOC client, image processing, repository
```

## HTTP API

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness probe. |
| GET | `/swpc/region?start=&end=` | Region observations in a UTC date range. |
| GET | `/swpc/region/{region}` | History for one region. |
| GET | `/swpc/region/{region}/event` | Events attributed to one region. |
| GET | `/swpc/event?start=&end=` | Solar events in a UTC datetime range. |
| GET | `/sdo/hmi?start=&end=` | HMI contour observations in a range. |
| GET | `/sdo/hmi/latest` | Most recent HMI observation (204 if none). |

Interactive docs at `/docs` (OpenAPI).

## Configuration

All settings are environment variables prefixed `PRESCIENT_` (see
`src/prescient/config.py`). The important one:

```
PRESCIENT_DATABASE_URL=postgresql+asyncpg://postgres@localhost:5432/prescient
```

## Development

Requires [uv](https://docs.astral.sh/uv/) and Docker.

```bash
uv sync                          # install deps into .venv

# bring up Postgres
docker compose up -d db

# apply migrations
uv run alembic upgrade head

# run the API and poller (separate terminals)
uv run prescient-api
uv run prescient-poller

# quality gates
uv run ruff check
uv run pyright
uv run pytest                    # uses testcontainers (real Postgres)
```

### Migrations

```bash
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
```

## Deployment

`docker compose up` builds and runs `db`, `api`, and `poller`. The `api`
container runs migrations on start; the `poller` waits for the schema.
