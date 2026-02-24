# PATSTAT Explorer - Configuration & Constants
# Extracted from app.py for modular structure

# =============================================================================
# COLOR PALETTE (Story 1.4 - UX Design Spec)
# =============================================================================
COLOR_PRIMARY = "#1E3A5F"
COLOR_SECONDARY = "#0A9396"
COLOR_ACCENT = "#FFB703"
COLOR_PALETTE = [COLOR_PRIMARY, COLOR_SECONDARY, COLOR_ACCENT, "#E63946", "#457B9D"]

# =============================================================================
# DEFAULT PARAMETER VALUES
# =============================================================================
DEFAULT_YEAR_START = 2014
DEFAULT_YEAR_END = 2023
DEFAULT_JURISDICTIONS = ["EP", "US", "DE"]
DEFAULT_TECH_FIELD = None

# Year range bounds for sliders and pickers
YEAR_MIN = 1782  # PATSTAT earliest patents (French patents from 1782)
YEAR_MAX = 2024

# =============================================================================
# UI CONSTANTS
# =============================================================================
# Category definitions for landing page pills (AC #1)
CATEGORIES = ["Overview", "Trends", "Regional", "Technology", "Performance", "Collaboration"]

# Stakeholder tags for filtering (Story 2.1)
STAKEHOLDER_TAGS = ["PATLIB", "BUSINESS", "UNIVERSITY"]

# Popular queries for "Common Questions" section (AC #3)
# Selection criteria: One query per category for balanced representation
COMMON_QUESTIONS = ["Q1B", "Q1C", "Q1E", "Q1I"]

# =============================================================================
# REFERENCE DATA
# =============================================================================
# Available jurisdictions for multiselect
JURISDICTIONS = ["EP", "US", "CN", "JP", "KR", "DE", "FR", "GB", "WO"]

# WIPO Technology Fields with sector grouping
# Source: WIPO IPC-Technology Concordance
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

# =============================================================================
# EXTERNAL URLS
# =============================================================================
TIP_PLATFORM_URL = "https://tip.epo.org"
GITHUB_REPO_URL = "https://github.com/herrkrueger/patstat"

# =============================================================================
# AI SYSTEM PROMPT
# =============================================================================
PATSTAT_SYSTEM_PROMPT = """You are an expert SQL query writer for EPO PATSTAT on BigQuery.

You have access to these main tables:
- tls201_appln: Patent applications (main table) - columns: appln_id, appln_auth, appln_filing_year, granted, docdb_family_id, docdb_family_size
- tls206_person: Applicants and inventors - columns: person_id, person_name, person_ctry_code, psn_sector, doc_std_name
- tls207_pers_appln: Links persons to applications - columns: person_id, appln_id, applt_seq_nr, invt_seq_nr
- tls209_appln_ipc: IPC classifications - columns: appln_id, ipc_class_symbol
- tls224_appln_cpc: CPC classifications - columns: appln_id, cpc_class_symbol
- tls211_pat_publn: Publications - columns: pat_publn_id, appln_id, publn_date, publn_first_grant
- tls212_citation: Citation data - columns: pat_publn_id, cited_pat_publn_id
- tls230_appln_techn_field: WIPO technology fields - columns: appln_id, techn_field_nr, weight
- tls901_techn_field_ipc: Technology field definitions - columns: techn_field_nr, techn_field, techn_sector
- tls801_country: Country codes - columns: ctry_code, st3_name

Generate BigQuery-compatible SQL that:
1. Uses proper table names with backticks
2. Includes appropriate JOINs
3. Has sensible LIMIT (default 50)
4. Handles NULLs appropriately
5. Returns results within 15 seconds typically

Respond in this exact format:
EXPLANATION:
[2-3 sentences explaining what the query does in plain language]

SQL:
```sql
[Your SQL query here]
```

NOTES:
[Any warnings or suggestions, or "None" if the query is straightforward]"""
