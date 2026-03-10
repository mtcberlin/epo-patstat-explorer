# Implementation Notes

Technical notes for developers working on PATSTAT Explorer.

## Series-based Query Architecture

### How queries are structured

Each query lives in `queries_bq.py` as an entry in the `QUERIES` dict. Queries are grouped into **series** — a collection of related queries that together form a complete analysis (like a report).

```
SERIES = {
    "S1": { "title": "Company Filing Strategy", "default_subject": "Airbus SE", ... }
}

QUERIES = {
    "Q1A": { "series": "S1", "title": "...", "sql": "...", "sql_template": "...", ... },
    "Q1B": { "series": "S1", ... },
    ...
}
```

**Naming convention:** `Q{series_number}{letter}` — e.g. Q1A through Q1J for Series 1.

### Static SQL vs Template SQL

Each query has two SQL fields:

- **`sql`**: The original, company-specific SQL (e.g. hardcoded Airbus name variants, fixed year ranges). Serves as reference — shown in the UI if no template exists.
- **`sql_template`**: Parameterized version using `@param` placeholders. This is what gets executed when the user clicks "Run Query". Shown in the SQL panel on the detail page.

The API (`api/main.py`) uses `sql_template` if available, otherwise falls back to `sql`.

### Parameter handling

Parameters are defined per query in the `parameters` dict. The frontend (`detail.js`) auto-generates controls based on type:

| Type | BigQuery Type | Frontend Control | SQL Usage |
|------|--------------|-----------------|-----------|
| `year_range` | 2× INT64 (`@year_start`, `@year_end`) | Dual range sliders | `BETWEEN @year_start AND @year_end` |
| `multiselect` | ARRAY\<STRING\> (`@param_name`) | Toggle buttons | `IN UNNEST(@param_name)` |
| `select` | STRING (`@param_name`) | Dropdown | `= @param_name` |
| `text` | STRING (`@param_name`) | Text input | `LIKE CONCAT('%', @param_name, '%')` |

### Company name matching pattern

All Series 1 queries use this pattern for the `company_name` text parameter:

```sql
WHERE (LOWER(p.person_name) LIKE CONCAT('%', LOWER(@company_name), '%')
       OR LOWER(p.han_name) LIKE CONCAT('%', LOWER(@company_name), '%'))
```

This searches both the raw `person_name` and the harmonized `han_name` fields in PATSTAT. Default is "airbus" but any company name works.

### Period comparison (auto-split)

Queries Q1C, Q1D, Q1E compare two time periods. The split point is computed automatically from the year range:

```sql
WITH split AS (
    SELECT @year_start + CAST(FLOOR((@year_end - @year_start - 1) / 2.0) AS INT64) AS mid
)
```

For `2014–2024`: mid = 2018, periods = 2014–2018 and 2019–2024.
For `2014–2023`: mid = 2018, periods = 2014–2018 and 2019–2023.

The period labels are generated dynamically using CONCAT and shown in the chart legend via the `color` field in the visualization config.

## Data Pipeline

```
queries_bq.py  →  scripts/export_queries.py  →  frontend/data/queries.json
                         ↑
                  modules/config.py (jurisdictions, tech_fields, categories)
```

After changing any query, run: `python3 scripts/export_queries.py`

The export script:
- Resolves option references ("jurisdictions" → actual list from config.py)
- Includes SERIES metadata in the JSON `meta` section
- Adds `series` field to each exported query
- Skips queries starting with "DQ" (draft queries)

## Visualization Config

Each query can have a `visualization` dict that tells ECharts what to render:

```python
"visualization": {
    "x": "column_name",          # X-axis data column
    "y": "column_name",          # Y-axis data column
    "color": "column_name",      # Optional: grouping column → multiple series
    "type": "bar|line|pie|stacked_bar",
    "stacked_columns": ["col1", "col2"],  # Optional: for wide-format stacked_bar
}
```

The `color` field creates:
- For `bar`: grouped bars (side-by-side per color value)
- For `line`: multiple line series
- For `stacked_bar`: stacked segments

Chart rendering happens in `frontend/js/detail.js` using ECharts 5 from CDN.

## Adding a New Query Series

1. Define the series in `queries_bq.py`:
   ```python
   SERIES["S2"] = {
       "id": "S2",
       "title": "University Research Comparison",
       "description": "...",
       "default_subject": "TU Munich vs KIT",
       "report_type": "university",
   }
   ```

2. Add queries with IDs `Q2A`, `Q2B`, etc. — each with `"series": "S2"`

3. Add any new categories to `modules/config.py` `CATEGORIES` list and corresponding CSS classes in `frontend/css/style.css`

4. Run `python3 scripts/export_queries.py` to regenerate `queries.json`

5. The landing page automatically groups by series (handled in `cards.js`)

## Local Development

```bash
# Start frontend (port 8080)
python3 -m http.server 8080 --directory frontend

# Start API (port 8000, with hot-reload)
.venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Run tests
.venv/bin/python -m pytest tests/test_query_metadata.py -v

# Export queries after changes
python3 scripts/export_queries.py
```

The frontend auto-detects the API URL: port 8080 → `http://localhost:8000/api`, otherwise `/api` (nginx proxy in production).

## Deployment

Docker Compose on Coolify (Hetzner). Auto-deploys from `main` branch.

- `docker-compose.yaml`: nginx (frontend, expose 80) + FastAPI (api, expose 8000)
- Frontend service gets the domain (patstatexplorer.depa.tech)
- API has no external domain — accessed via nginx proxy (`/api/ → api:8000/api/`)
- GCP credentials: `GOOGLE_APPLICATION_CREDENTIALS_JSON` env var in Coolify (Is Literal + Is Multiline)
