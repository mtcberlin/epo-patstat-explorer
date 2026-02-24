"""PATSTAT Explorer API — FastAPI backend for BigQuery execution."""
import json
import os
import sys
import time
from decimal import Decimal
from datetime import date, datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.cloud import bigquery
from google.oauth2 import service_account

# Add parent directory to path for query imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from queries_bq import QUERIES

# Import config directly to avoid Streamlit dependency in modules/__init__.py
import importlib.util as _ilu
_cfg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "modules", "config.py")
_spec = _ilu.spec_from_file_location("config", _cfg_path)
_config = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_config)
JURISDICTIONS = _config.JURISDICTIONS
TECH_FIELDS = _config.TECH_FIELDS

app = FastAPI(title="PATSTAT Explorer API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# BigQuery Client
# ============================================================
_bq_client = None


def get_bq_client():
    global _bq_client
    if _bq_client is not None:
        return _bq_client

    project = os.getenv("BIGQUERY_PROJECT", "patstat-mtc")
    creds_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if creds_json:
        info = json.loads(creds_json)
        credentials = service_account.Credentials.from_service_account_info(info)
        _bq_client = bigquery.Client(project=project, credentials=credentials)
    elif creds_path:
        credentials = service_account.Credentials.from_service_account_file(creds_path)
        _bq_client = bigquery.Client(project=project, credentials=credentials)
    else:
        _bq_client = bigquery.Client(project=project)

    return _bq_client


def resolve_options(options):
    if options == "jurisdictions":
        return JURISDICTIONS
    elif options == "wipo_fields":
        return [str(k) for k in sorted(TECH_FIELDS.keys())]
    return options if isinstance(options, list) else []


# ============================================================
# Request / Response Models
# ============================================================
class ExecuteRequest(BaseModel):
    query_id: str
    parameters: dict = {}


# ============================================================
# Endpoints
# ============================================================
@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


@app.post("/api/execute")
def execute_query(req: ExecuteRequest):
    query_def = QUERIES.get(req.query_id)
    if not query_def:
        raise HTTPException(404, f"Query {req.query_id} not found")

    sql_template = query_def.get("sql_template") or query_def.get("sql")
    if not sql_template:
        raise HTTPException(400, "No SQL defined for this query")

    # Build BigQuery query parameters
    query_params = []
    param_defs = query_def.get("parameters", {})

    for param_name, param_def in param_defs.items():
        ptype = param_def["type"]

        if ptype == "year_range":
            year_start = req.parameters.get(
                "year_start", param_def.get("default_start", 2014)
            )
            year_end = req.parameters.get(
                "year_end", param_def.get("default_end", 2023)
            )
            query_params.append(
                bigquery.ScalarQueryParameter("year_start", "INT64", int(year_start))
            )
            query_params.append(
                bigquery.ScalarQueryParameter("year_end", "INT64", int(year_end))
            )

        elif ptype == "multiselect":
            values = req.parameters.get(param_name, param_def.get("defaults", []))
            if isinstance(values, str):
                values = [values]
            query_params.append(
                bigquery.ArrayQueryParameter(param_name, "STRING", values)
            )

        elif ptype == "select":
            value = req.parameters.get(param_name, param_def.get("defaults", ""))
            query_params.append(
                bigquery.ScalarQueryParameter(param_name, "STRING", str(value))
            )

        elif ptype == "text":
            value = req.parameters.get(param_name, param_def.get("defaults", ""))
            query_params.append(
                bigquery.ScalarQueryParameter(param_name, "STRING", str(value))
            )

    # Execute query
    client = get_bq_client()
    dataset = os.getenv("BIGQUERY_DATASET", "patstat")

    job_config = bigquery.QueryJobConfig(
        query_parameters=query_params,
        default_dataset=f"{client.project}.{dataset}",
    )

    start_time = time.time()
    try:
        query_job = client.query(sql_template, job_config=job_config)
        results = query_job.result()
        execution_time = round(time.time() - start_time, 2)

        columns = [field.name for field in results.schema] if results.schema else []
        rows = []
        for row in results:
            r = {}
            for col in columns:
                val = row[col]
                # Convert non-JSON-serializable types
                if isinstance(val, Decimal):
                    val = float(val)
                elif isinstance(val, (date, datetime)):
                    val = val.isoformat()
                elif isinstance(val, bytes):
                    val = val.decode("utf-8", errors="replace")
                r[col] = val
            rows.append(r)

        return {
            "data": rows,
            "columns": columns,
            "row_count": len(rows),
            "execution_time": execution_time,
        }
    except Exception as e:
        return {
            "error": str(e),
            "data": [],
            "columns": [],
            "row_count": 0,
            "execution_time": round(time.time() - start_time, 2),
        }
