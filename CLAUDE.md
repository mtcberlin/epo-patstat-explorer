# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

PATSTAT Explorer is a web app that lets patent information professionals explore EPO PATSTAT data (450 GB, 27+ tables on BigQuery) through pre-built parameterized queries, without writing SQL.

**Stack:** Static HTML/CSS/JS frontend + FastAPI backend + Nginx reverse proxy
**Live:** patstatexplorer.depa.tech | **License:** MIT

## File Structure

```
frontend/           Static HTML/CSS/JS served by Nginx
  index.html        Landing page — query cards grid
  query.html        Query detail page — parameters, execution, results
  ai.html           AI Query Builder page (frontend only, backend TBD — see #20)
  css/style.css     All styles
  js/main.js        Shared utilities, API client
  js/cards.js       Landing page card rendering
  js/detail.js      Query detail page logic
  data/queries.json Exported query metadata for frontend
  assets/           Favicons, logos

api/                FastAPI backend
  main.py           All endpoints: /api/health, /api/execute
  requirements.txt  Python deps (fastapi, uvicorn, google-cloud-bigquery)

queries_bq.py       Single source of truth — all queries with metadata, SQL, parameters, visualization config
scripts/            BigQuery migration utilities, query export script
tests/              pytest tests (currently: test_query_metadata.py)
docs/               Implementation notes

docker-compose.yaml Orchestrates frontend (Nginx) + API (uvicorn)
Dockerfile.api      API container
Dockerfile.frontend Frontend container (Nginx)
nginx.conf          Routes /api/* → FastAPI, /* → static files
```

## Commands

```bash
# Run locally with Docker
docker-compose up --build

# Run API standalone (development)
cd api && uvicorn main:app --reload --port 8000

# Run tests
pytest tests/ -v

# Export queries.json from queries_bq.py
python scripts/export_queries.py
```

## Architecture

**Query-as-Data:** Each query in `queries_bq.py` QUERIES dict has: `title`, `tags`, `category`, `series`, `description`, `explanation`, `sql`, `sql_template`, `parameters`, `visualization`, `platforms`, timing estimates. Adding a query = adding a dict entry.

**Parameter types:** `year_range` (→ `@year_start`/`@year_end` INT64), `multiselect` (→ `ARRAY<STRING>` with `IN UNNEST(@param)`), `select` (→ STRING), `text` (→ STRING).

**Series:** Queries are grouped into series (e.g., S1: Company Filing Strategy). Each series has `title` and `description` in the `SERIES` dict.

**API flow:** Frontend → `/api/execute` with `{query_id, parameters}` → FastAPI builds BigQuery parameterized query → returns `{data, columns, row_count, execution_time}`.

## BigQuery Schema

EPO PATSTAT 2025 Autumn in `patstat-mtc.patstat`. Key tables: `tls201_appln` (applications), `tls206_person` (applicants/inventors), `tls207_pers_appln` (person-application links), `tls209_appln_ipc` (IPC), `tls224_appln_cpc` (CPC), `tls230_appln_techn_field` (WIPO fields), `tls211_pat_publn` (publications), `tls212_citation` (citations).

## Configuration

Local dev uses `.env` (see `.env.example`). Key vars: `BIGQUERY_PROJECT`, `BIGQUERY_DATASET`, `GOOGLE_APPLICATION_CREDENTIALS_JSON`.

## Workflow

- Branch: `develop` → PR → `main` (branch protection on main)
- Deployment: Coolify on Hetzner, auto-deploys from `main`
- Tracking: GitHub Issues + Jira PIP-63

## Open Feature Issues

- #19: CSV download for query results (P1)
- #20: AI Query Builder backend (P1)
- #21: TIP Export — SQL → Jupyter notebook (P2)
- #22: URL-shareable query parameters (P2)
- #23: Auto-generate insight headlines (P3)
- #24: Evaluate Contribute System need (P3)
