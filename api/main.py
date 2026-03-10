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

# Reference data for parameter resolution
JURISDICTIONS = ["EP", "US", "CN", "JP", "KR", "DE", "FR", "GB", "WO"]
TECH_FIELDS = {
    1: ("Electrical machinery, apparatus, energy", "Electrical engineering"),
    2: ("Audio-visual technology", "Electrical engineering"),
    3: ("Telecommunications", "Electrical engineering"),
    4: ("Digital communication", "Electrical engineering"),
    5: ("Basic communication processes", "Electrical engineering"),
    6: ("Computer technology", "Electrical engineering"),
    7: ("IT methods for management", "Electrical engineering"),
    8: ("Semiconductors", "Electrical engineering"),
    9: ("Optics", "Instruments"),
    10: ("Measurement", "Instruments"),
    11: ("Analysis of biological materials", "Instruments"),
    12: ("Control", "Instruments"),
    13: ("Medical technology", "Instruments"),
    14: ("Organic fine chemistry", "Chemistry"),
    15: ("Biotechnology", "Chemistry"),
    16: ("Pharmaceuticals", "Chemistry"),
    17: ("Macromolecular chemistry, polymers", "Chemistry"),
    18: ("Food chemistry", "Chemistry"),
    19: ("Basic materials chemistry", "Chemistry"),
    20: ("Materials, metallurgy", "Chemistry"),
    21: ("Surface technology, coating", "Chemistry"),
    22: ("Micro-structural and nano-technology", "Chemistry"),
    23: ("Chemical engineering", "Chemistry"),
    24: ("Environmental technology", "Chemistry"),
    25: ("Handling", "Mechanical engineering"),
    26: ("Machine tools", "Mechanical engineering"),
    27: ("Engines, pumps, turbines", "Mechanical engineering"),
    28: ("Textile and paper machines", "Mechanical engineering"),
    29: ("Other special machines", "Mechanical engineering"),
    30: ("Thermal processes and apparatus", "Mechanical engineering"),
    31: ("Mechanical elements", "Mechanical engineering"),
    32: ("Transport", "Mechanical engineering"),
    33: ("Furniture, games", "Other fields"),
    34: ("Other consumer goods", "Other fields"),
    35: ("Civil engineering", "Other fields"),
}

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
