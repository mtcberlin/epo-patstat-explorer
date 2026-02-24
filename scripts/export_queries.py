#!/usr/bin/env python3
"""Export queries from queries_bq.py to queries.json for the static frontend."""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from queries_bq import QUERIES

# Import config directly to avoid Streamlit dependency in modules/__init__.py
import importlib.util
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "modules", "config.py")
spec = importlib.util.spec_from_file_location("config", config_path)
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

JURISDICTIONS = config.JURISDICTIONS
TECH_FIELDS = config.TECH_FIELDS
CATEGORIES = config.CATEGORIES
STAKEHOLDER_TAGS = config.STAKEHOLDER_TAGS


def resolve_options(options):
    """Resolve string references to actual option lists."""
    if options == "jurisdictions":
        return JURISDICTIONS
    elif options == "wipo_fields":
        return [str(k) for k in sorted(TECH_FIELDS.keys())]
    elif isinstance(options, list):
        return options
    return options


def export_queries():
    output = {
        "meta": {
            "categories": CATEGORIES,
            "stakeholder_tags": STAKEHOLDER_TAGS,
            "jurisdictions": JURISDICTIONS,
            "tech_fields": {
                str(k): {"name": v[0], "sector": v[1]}
                for k, v in TECH_FIELDS.items()
            },
        },
        "queries": {},
    }

    for qid, query in QUERIES.items():
        if qid.startswith("DQ"):
            continue

        q = {
            "id": qid,
            "title": query["title"],
            "tags": query.get("tags", []),
            "category": query.get("category", ""),
            "description": query.get("description", ""),
            "explanation": query.get("explanation", ""),
            "key_outputs": query.get("key_outputs", []),
            "platforms": query.get("platforms", ["bigquery"]),
            "estimated_seconds_first_run": query.get("estimated_seconds_first_run", 10),
            "estimated_seconds_cached": query.get("estimated_seconds_cached", 5),
            "visualization": query.get("visualization"),
            "display_mode": query.get("display_mode"),
            "sql": query.get("sql", "").strip(),
            "sql_template": query.get("sql_template", "").strip(),
            "parameters": {},
        }

        for param_name, param_def in query.get("parameters", {}).items():
            p = dict(param_def)
            if "options" in p:
                p["options"] = resolve_options(p["options"])
            q["parameters"][param_name] = p

        output["queries"][qid] = q

    return output


if __name__ == "__main__":
    data = export_queries()
    output_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "frontend",
        "data",
        "queries.json",
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Exported {len(data['queries'])} queries to {output_path}")
