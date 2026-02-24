"""
PATSTAT Queries — Series-based query library for PATSTAT Explorer.

Series Naming:
- Q1x: Company Filing Strategy Analysis (default: Airbus SE)
- Q2x: (planned) University Research Comparison
- Q3x: (planned) ...

Parameter Types:
- year_range: Year slider → @year_start/@year_end (INT64)
- multiselect: Multiple selection → @param (ARRAY<STRING>)
- text: Text input → @param (STRING)
"""

STAKEHOLDERS = {
    "PATLIB": "Patent Information Centers & Libraries",
    "BUSINESS": "Companies & Industry",
    "UNIVERSITY": "Universities & Research",
}

SERIES = {
    "S1": {
        "id": "S1",
        "title": "Company Filing Strategy",
        "description": "Comprehensive patent strategy analysis of a large industrial company. "
                       "10 queries covering filing trends, geographic strategy, technology shifts, "
                       "grant rates, R&D collaborations, and inventor locations.",
        "default_subject": "Airbus SE",
        "report_type": "company",
    },
}

QUERIES = {

    # =========================================================================
    # S1: COMPANY FILING STRATEGY (default: Airbus SE)
    # =========================================================================

    "Q1A": {
        "title": "Which name variants exist in PATSTAT?",
        "tags": ["PATLIB"],
        "series": "S1",
        "category": "Overview",
        "platforms": ["bigquery"],
        "description": "Identify all name variants of a company in PATSTAT with application counts per variant",
        "explanation": """First exploration to understand the applicant landscape.
Large companies have many name variants through renamings, subsidiaries, and mergers.
- Shows person_name, harmonized name (han_name), and standardized name (psn_name)
- Counts distinct applications per variant
- Filters to variants with at least 5 applications

For Airbus: includes Airbus Operations, Defence & Space, Helicopters, plus historical names
(EADS, Eurocopter, Astrium, Cassidian).""",
        "key_outputs": [
            "Name variants with application counts",
            "Country codes per entity",
            "First and last filing year per variant",
            "PSN sector classification",
        ],
        "estimated_seconds_first_run": 5,
        "estimated_seconds_cached": 2,
        "visualization": None,
        "display_mode": None,
        "parameters": {
            "company_name": {
                "type": "text",
                "label": "Company Name",
                "defaults": "airbus",
                "placeholder": "e.g. airbus, boeing, siemens",
                "required": True,
            },
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2000,
                "default_end": 2024,
                "required": False,
            },
        },
        "sql": """SELECT
    p.person_name,
    p.han_name,
    p.psn_name,
    p.psn_sector,
    p.person_ctry_code,
    COUNT(DISTINCT pa.appln_id) AS applications,
    MIN(a.appln_filing_year) AS first_filing_year,
    MAX(a.appln_filing_year) AS last_filing_year
FROM tls206_person p
JOIN tls207_pers_appln pa ON p.person_id = pa.person_id
JOIN tls201_appln a ON pa.appln_id = a.appln_id
WHERE pa.applt_seq_nr > 0
  AND (
    LOWER(p.person_name) LIKE '%airbus%'
    OR LOWER(p.han_name) LIKE '%airbus%'
    OR LOWER(p.person_name) LIKE '%eurocopter%'
    OR LOWER(p.person_name) LIKE '%astrium%'
    OR LOWER(p.person_name) LIKE '%cassidian%'
    OR (LOWER(p.person_name) LIKE '%eads%'
        AND LOWER(p.person_name) NOT LIKE '%beads%'
        AND LOWER(p.person_name) NOT LIKE '%leads%'
        AND LOWER(p.person_name) NOT LIKE '%heads%')
  )
  AND a.appln_filing_year >= 2000
GROUP BY p.person_name, p.han_name, p.psn_name, p.psn_sector, p.person_ctry_code
HAVING COUNT(DISTINCT pa.appln_id) >= 5
ORDER BY applications DESC
LIMIT 100""",
        "sql_template": """SELECT
    p.person_name,
    p.han_name,
    p.psn_name,
    p.psn_sector,
    p.person_ctry_code,
    COUNT(DISTINCT pa.appln_id) AS applications,
    MIN(a.appln_filing_year) AS first_filing_year,
    MAX(a.appln_filing_year) AS last_filing_year
FROM tls206_person p
JOIN tls207_pers_appln pa ON p.person_id = pa.person_id
JOIN tls201_appln a ON pa.appln_id = a.appln_id
WHERE pa.applt_seq_nr > 0
  AND (LOWER(p.person_name) LIKE CONCAT('%', LOWER(@company_name), '%')
       OR LOWER(p.han_name) LIKE CONCAT('%', LOWER(@company_name), '%'))
  AND a.appln_filing_year BETWEEN @year_start AND @year_end
GROUP BY p.person_name, p.han_name, p.psn_name, p.psn_sector, p.person_ctry_code
HAVING COUNT(DISTINCT pa.appln_id) >= 5
ORDER BY applications DESC
LIMIT 100""",
    },

    "Q1B": {
        "title": "How has filing activity changed over time?",
        "tags": ["PATLIB", "BUSINESS"],
        "series": "S1",
        "category": "Trends",
        "platforms": ["bigquery"],
        "description": "Patent filing trend by year and business unit, using DOCDB families to avoid double-counting",
        "explanation": """Shows the overall patent filing activity over time, broken down by business unit.
Counts DOCDB families (not individual applications) to avoid counting the same invention multiple times.

The business unit assignment is based on applicant name matching:
- Operations = core manufacturing division
- Defence & Space, Helicopters = named divisions
- Group/Holding = corporate entity
- Main/Other = unmatched or parent entity

Note: 2024 data may be incomplete due to PATSTAT publication delay (~18 months).""",
        "key_outputs": [
            "Patent families per year",
            "Total applications per year",
            "Breakdown by business unit",
            "Average family size trend",
        ],
        "estimated_seconds_first_run": 8,
        "estimated_seconds_cached": 3,
        "visualization": {
            "x": "appln_filing_year",
            "y": "total_applications",
            "color": "business_unit",
            "type": "stacked_bar",
        },
        "display_mode": None,
        "parameters": {
            "company_name": {
                "type": "text",
                "label": "Company Name",
                "defaults": "airbus",
                "placeholder": "e.g. airbus, boeing, siemens",
                "required": True,
            },
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2024,
                "required": True,
            },
        },
        "sql": """WITH airbus_apps AS (
    SELECT DISTINCT
        a.appln_id,
        a.docdb_family_id,
        a.appln_filing_year,
        a.appln_auth,
        a.granted,
        a.docdb_family_size,
        CASE
            WHEN LOWER(p.person_name) LIKE '%airbus operations%' THEN 'Airbus Operations'
            WHEN LOWER(p.person_name) LIKE '%airbus defence%'
              OR LOWER(p.person_name) LIKE '%airbus defense%' THEN 'Defence & Space'
            WHEN LOWER(p.person_name) LIKE '%airbus helicopter%'
              OR LOWER(p.person_name) LIKE '%eurocopter%' THEN 'Helicopters'
            WHEN LOWER(p.person_name) LIKE '%airbus group%' THEN 'Group (Holding)'
            WHEN LOWER(p.person_name) LIKE '%airbus s%a%s%' THEN 'SAS (HQ)'
            WHEN LOWER(p.person_name) LIKE '%astrium%' THEN 'Astrium (→ Defence & Space)'
            WHEN LOWER(p.person_name) LIKE '%cassidian%' THEN 'Cassidian (→ Defence & Space)'
            WHEN LOWER(p.person_name) LIKE '%eads%' THEN 'EADS (→ Airbus Group)'
            ELSE 'Airbus (other)'
        END AS business_unit
    FROM tls201_appln a
    JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
    JOIN tls206_person p ON pa.person_id = p.person_id
    WHERE pa.applt_seq_nr > 0
      AND a.appln_filing_year BETWEEN 2014 AND 2024
      AND (
        LOWER(p.person_name) LIKE '%airbus%'
        OR LOWER(p.person_name) LIKE '%eurocopter%'
        OR LOWER(p.person_name) LIKE '%astrium%'
        OR LOWER(p.person_name) LIKE '%cassidian%'
        OR (LOWER(p.person_name) LIKE '%eads%'
            AND LOWER(p.person_name) NOT LIKE '%beads%'
            AND LOWER(p.person_name) NOT LIKE '%leads%'
            AND LOWER(p.person_name) NOT LIKE '%heads%')
      )
)
SELECT
    appln_filing_year,
    business_unit,
    COUNT(DISTINCT docdb_family_id) AS patent_families,
    COUNT(DISTINCT appln_id) AS total_applications,
    COUNT(DISTINCT CASE WHEN granted = 'Y' THEN appln_id END) AS granted_applications,
    ROUND(AVG(docdb_family_size), 1) AS avg_family_size
FROM airbus_apps
GROUP BY appln_filing_year, business_unit
ORDER BY appln_filing_year, patent_families DESC""",
        "sql_template": """WITH company_apps AS (
    SELECT DISTINCT
        a.appln_id,
        a.docdb_family_id,
        a.appln_filing_year,
        a.granted,
        a.docdb_family_size,
        CASE
            WHEN LOWER(p.person_name) LIKE CONCAT('%', LOWER(@company_name), ' operations%') THEN 'Operations'
            WHEN LOWER(p.person_name) LIKE CONCAT('%', LOWER(@company_name), ' defence%')
              OR LOWER(p.person_name) LIKE CONCAT('%', LOWER(@company_name), ' defense%') THEN 'Defence & Space'
            WHEN LOWER(p.person_name) LIKE CONCAT('%', LOWER(@company_name), ' helicopter%') THEN 'Helicopters'
            WHEN LOWER(p.person_name) LIKE CONCAT('%', LOWER(@company_name), ' group%') THEN 'Group'
            ELSE 'Main / Other'
        END AS business_unit
    FROM tls201_appln a
    JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
    JOIN tls206_person p ON pa.person_id = p.person_id
    WHERE pa.applt_seq_nr > 0
      AND a.appln_filing_year BETWEEN @year_start AND @year_end
      AND (LOWER(p.person_name) LIKE CONCAT('%', LOWER(@company_name), '%')
           OR LOWER(p.han_name) LIKE CONCAT('%', LOWER(@company_name), '%'))
)
SELECT
    appln_filing_year,
    business_unit,
    COUNT(DISTINCT docdb_family_id) AS patent_families,
    COUNT(DISTINCT appln_id) AS total_applications,
    COUNT(DISTINCT CASE WHEN granted = 'Y' THEN appln_id END) AS granted_applications,
    ROUND(AVG(docdb_family_size), 1) AS avg_family_size
FROM company_apps
GROUP BY appln_filing_year, business_unit
ORDER BY appln_filing_year, patent_families DESC""",
    },

    "Q1C": {
        "title": "Where does the company file patents?",
        "tags": ["BUSINESS"],
        "series": "S1",
        "category": "Regional",
        "platforms": ["bigquery"],
        "description": "Geographic filing strategy — patent office distribution with period comparison",
        "explanation": """Compares the geographic filing strategy between two time periods (auto-split at midpoint).
Shows which patent offices receive applications and how the strategy shifts over time.

Key patterns to look for:
- Shift from national offices (DPMA, INPI) to EPO (more efficient, covers 39 states)
- Growth in Asian markets (CN, KR, JP)
- Decline in certain regions (consolidation)

The year range is automatically split into two equal periods for comparison.""",
        "key_outputs": [
            "Applications per patent office per period",
            "Patent families per office",
            "Period-over-period comparison",
        ],
        "estimated_seconds_first_run": 8,
        "estimated_seconds_cached": 3,
        "visualization": {
            "x": "appln_auth",
            "y": "applications",
            "color": "period",
            "type": "bar",
        },
        "display_mode": None,
        "parameters": {
            "company_name": {
                "type": "text",
                "label": "Company Name",
                "defaults": "airbus",
                "placeholder": "e.g. airbus, boeing, siemens",
                "required": True,
            },
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2024,
                "required": True,
            },
        },
        "sql": """WITH airbus_apps AS (
    SELECT DISTINCT
        a.appln_id,
        a.docdb_family_id,
        a.appln_auth,
        a.appln_filing_year,
        CASE
            WHEN a.appln_filing_year BETWEEN 2014 AND 2018 THEN '2014–2018'
            WHEN a.appln_filing_year BETWEEN 2019 AND 2024 THEN '2019–2024'
        END AS period
    FROM tls201_appln a
    JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
    JOIN tls206_person p ON pa.person_id = p.person_id
    WHERE pa.applt_seq_nr > 0
      AND a.appln_filing_year BETWEEN 2014 AND 2024
      AND (
        LOWER(p.person_name) LIKE '%airbus%'
        OR LOWER(p.person_name) LIKE '%eurocopter%'
        OR LOWER(p.person_name) LIKE '%astrium%'
      )
)
SELECT
    appln_auth,
    period,
    COUNT(DISTINCT docdb_family_id) AS families,
    COUNT(DISTINCT appln_id) AS applications
FROM airbus_apps
WHERE period IS NOT NULL
GROUP BY appln_auth, period
HAVING COUNT(DISTINCT appln_id) >= 10
ORDER BY applications DESC""",
        "sql_template": """WITH split AS (
    SELECT @year_start + CAST(FLOOR((@year_end - @year_start - 1) / 2.0) AS INT64) AS mid
),
company_apps AS (
    SELECT DISTINCT
        a.appln_id,
        a.docdb_family_id,
        a.appln_auth,
        CASE
            WHEN a.appln_filing_year <= (SELECT mid FROM split)
            THEN CONCAT(CAST(@year_start AS STRING), '–', CAST((SELECT mid FROM split) AS STRING))
            ELSE CONCAT(CAST((SELECT mid FROM split) + 1 AS STRING), '–', CAST(@year_end AS STRING))
        END AS period
    FROM tls201_appln a
    JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
    JOIN tls206_person p ON pa.person_id = p.person_id
    WHERE pa.applt_seq_nr > 0
      AND a.appln_filing_year BETWEEN @year_start AND @year_end
      AND (LOWER(p.person_name) LIKE CONCAT('%', LOWER(@company_name), '%')
           OR LOWER(p.han_name) LIKE CONCAT('%', LOWER(@company_name), '%'))
)
SELECT
    appln_auth,
    period,
    COUNT(DISTINCT docdb_family_id) AS families,
    COUNT(DISTINCT appln_id) AS applications
FROM company_apps
GROUP BY appln_auth, period
HAVING COUNT(DISTINCT appln_id) >= 5
ORDER BY applications DESC""",
    },

    "Q1D": {
        "title": "Which technology fields are shifting?",
        "tags": ["BUSINESS", "UNIVERSITY"],
        "series": "S1",
        "category": "Technology",
        "platforms": ["bigquery"],
        "description": "WIPO technology field analysis with period comparison showing strategic shifts",
        "explanation": """Maps patents to the 35 WIPO technology fields and compares two periods.
Uses tls230_appln_techn_field for classification and tls901_techn_field_ipc for field names.

Key questions this answers:
- Which technology sectors dominate the portfolio?
- Is the company shifting towards digitalization, sustainability, or new areas?
- Which legacy technology areas are declining?

The year range is automatically split into two equal periods.""",
        "key_outputs": [
            "Technology field ranking by application count",
            "Period comparison (early vs recent)",
            "Sector grouping (Electrical, Instruments, Chemistry, Mechanical, Other)",
        ],
        "estimated_seconds_first_run": 10,
        "estimated_seconds_cached": 3,
        "visualization": {
            "x": "techn_field",
            "y": "applications",
            "color": "period",
            "type": "bar",
        },
        "display_mode": None,
        "parameters": {
            "company_name": {
                "type": "text",
                "label": "Company Name",
                "defaults": "airbus",
                "placeholder": "e.g. airbus, boeing, siemens",
                "required": True,
            },
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2024,
                "required": True,
            },
        },
        "sql": """WITH airbus_apps AS (
    SELECT DISTINCT
        a.appln_id,
        a.appln_filing_year,
        CASE
            WHEN a.appln_filing_year BETWEEN 2014 AND 2018 THEN 'early'
            WHEN a.appln_filing_year BETWEEN 2019 AND 2024 THEN 'recent'
        END AS period
    FROM tls201_appln a
    JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
    JOIN tls206_person p ON pa.person_id = p.person_id
    WHERE pa.applt_seq_nr > 0
      AND a.appln_filing_year BETWEEN 2014 AND 2024
      AND LOWER(p.person_name) LIKE '%airbus%'
),
tech_by_period AS (
    SELECT
        tfi.techn_sector,
        tfi.techn_field,
        tf.techn_field_nr,
        aa.period,
        COUNT(DISTINCT aa.appln_id) AS applications
    FROM airbus_apps aa
    JOIN tls230_appln_techn_field tf ON aa.appln_id = tf.appln_id
    JOIN tls901_techn_field_ipc tfi ON tf.techn_field_nr = tfi.techn_field_nr
    WHERE aa.period IS NOT NULL
    GROUP BY tfi.techn_sector, tfi.techn_field, tf.techn_field_nr, aa.period
)
SELECT
    techn_sector,
    techn_field,
    MAX(CASE WHEN period = 'early' THEN applications END) AS apps_2014_2018,
    MAX(CASE WHEN period = 'recent' THEN applications END) AS apps_2019_2024,
    ROUND(
        SAFE_DIVIDE(
            MAX(CASE WHEN period = 'recent' THEN applications END) -
            MAX(CASE WHEN period = 'early' THEN applications END),
            MAX(CASE WHEN period = 'early' THEN applications END)
        ) * 100, 1
    ) AS growth_percent
FROM tech_by_period
GROUP BY techn_sector, techn_field
HAVING COALESCE(MAX(CASE WHEN period = 'early' THEN applications END), 0) +
       COALESCE(MAX(CASE WHEN period = 'recent' THEN applications END), 0) >= 20
ORDER BY growth_percent DESC NULLS LAST""",
        "sql_template": """WITH split AS (
    SELECT @year_start + CAST(FLOOR((@year_end - @year_start - 1) / 2.0) AS INT64) AS mid
),
company_apps AS (
    SELECT DISTINCT
        a.appln_id,
        CASE
            WHEN a.appln_filing_year <= (SELECT mid FROM split)
            THEN CONCAT(CAST(@year_start AS STRING), '–', CAST((SELECT mid FROM split) AS STRING))
            ELSE CONCAT(CAST((SELECT mid FROM split) + 1 AS STRING), '–', CAST(@year_end AS STRING))
        END AS period
    FROM tls201_appln a
    JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
    JOIN tls206_person p ON pa.person_id = p.person_id
    WHERE pa.applt_seq_nr > 0
      AND a.appln_filing_year BETWEEN @year_start AND @year_end
      AND (LOWER(p.person_name) LIKE CONCAT('%', LOWER(@company_name), '%')
           OR LOWER(p.han_name) LIKE CONCAT('%', LOWER(@company_name), '%'))
)
SELECT
    tfi.techn_sector,
    tfi.techn_field,
    ca.period,
    COUNT(DISTINCT ca.appln_id) AS applications
FROM company_apps ca
JOIN tls230_appln_techn_field tf ON ca.appln_id = tf.appln_id
JOIN tls901_techn_field_ipc tfi ON tf.techn_field_nr = tfi.techn_field_nr
GROUP BY tfi.techn_sector, tfi.techn_field, ca.period
HAVING COUNT(DISTINCT ca.appln_id) >= 10
ORDER BY applications DESC""",
    },

    "Q1E": {
        "title": "What are the top IPC classes and trends?",
        "tags": ["PATLIB", "BUSINESS"],
        "series": "S1",
        "category": "Technology",
        "platforms": ["bigquery"],
        "description": "Top 20 IPC main classes with period comparison — shows concrete technology investments",
        "explanation": """Extracts IPC main classes (4 characters, e.g. B64C = Aeroplanes) and compares two periods.
More specific than WIPO technology fields — shows exact patent classification codes.

For aerospace companies, typical dominant classes:
- B64C/D/F = Aircraft, equipment, ground handling
- F02C/K = Gas turbines, jet engines
- G06F/N = Computing, AI
- H04L/B = Data transmission, communications
- B29C = Composite processing
- G01S = Radar/navigation

The year range is automatically split into two equal periods.""",
        "key_outputs": [
            "Top 20 IPC classes by total volume",
            "Period comparison with growth percentage",
            "Human-readable IPC descriptions",
        ],
        "estimated_seconds_first_run": 10,
        "estimated_seconds_cached": 3,
        "visualization": {
            "x": "ipc_main_class",
            "y": "applications",
            "color": "period",
            "type": "bar",
        },
        "display_mode": None,
        "parameters": {
            "company_name": {
                "type": "text",
                "label": "Company Name",
                "defaults": "airbus",
                "placeholder": "e.g. airbus, boeing, siemens",
                "required": True,
            },
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2024,
                "required": True,
            },
        },
        "sql": """WITH airbus_apps AS (
    SELECT DISTINCT
        a.appln_id,
        a.appln_filing_year,
        CASE
            WHEN a.appln_filing_year BETWEEN 2014 AND 2018 THEN 'early'
            WHEN a.appln_filing_year BETWEEN 2019 AND 2024 THEN 'recent'
        END AS period
    FROM tls201_appln a
    JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
    JOIN tls206_person p ON pa.person_id = p.person_id
    WHERE pa.applt_seq_nr > 0
      AND a.appln_filing_year BETWEEN 2014 AND 2024
      AND LOWER(p.person_name) LIKE '%airbus%'
),
ipc_analysis AS (
    SELECT
        SUBSTR(ipc.ipc_class_symbol, 1, 4) AS ipc_main_class,
        aa.period,
        COUNT(DISTINCT aa.appln_id) AS applications
    FROM airbus_apps aa
    JOIN tls209_appln_ipc ipc ON aa.appln_id = ipc.appln_id
    WHERE aa.period IS NOT NULL
    GROUP BY SUBSTR(ipc.ipc_class_symbol, 1, 4), aa.period
)
SELECT
    ipc_main_class,
    CASE ipc_main_class
        WHEN 'B64C' THEN 'Aeroplanes/Helicopters'
        WHEN 'B64D' THEN 'Aircraft equipment'
        WHEN 'B64F' THEN 'Ground handling'
        WHEN 'B64G' THEN 'Cosmonautics'
        WHEN 'F02C' THEN 'Gas turbines'
        WHEN 'F02K' THEN 'Jet engines'
        WHEN 'G01S' THEN 'Radar/Navigation'
        WHEN 'G06F' THEN 'Computing'
        WHEN 'G06N' THEN 'AI/Neural networks'
        WHEN 'H04L' THEN 'Data transmission'
        WHEN 'H04B' THEN 'Telecom'
        WHEN 'B29C' THEN 'Composites'
        WHEN 'G05B' THEN 'Control systems'
        WHEN 'G05D' THEN 'Regulation'
        WHEN 'H01Q' THEN 'Antennas'
        WHEN 'B32B' THEN 'Layered materials'
        WHEN 'H01M' THEN 'Batteries/Fuel cells'
        WHEN 'H02J' THEN 'Energy distribution'
        ELSE ipc_main_class
    END AS description,
    COALESCE(MAX(CASE WHEN period = 'early' THEN applications END), 0) AS apps_2014_2018,
    COALESCE(MAX(CASE WHEN period = 'recent' THEN applications END), 0) AS apps_2019_2024,
    COALESCE(MAX(CASE WHEN period = 'early' THEN applications END), 0) +
    COALESCE(MAX(CASE WHEN period = 'recent' THEN applications END), 0) AS total,
    ROUND(
        SAFE_DIVIDE(
            MAX(CASE WHEN period = 'recent' THEN applications END) -
            MAX(CASE WHEN period = 'early' THEN applications END),
            MAX(CASE WHEN period = 'early' THEN applications END)
        ) * 100, 1
    ) AS growth_percent
FROM ipc_analysis
GROUP BY ipc_main_class
HAVING COALESCE(MAX(CASE WHEN period = 'early' THEN applications END), 0) +
       COALESCE(MAX(CASE WHEN period = 'recent' THEN applications END), 0) >= 20
ORDER BY total DESC
LIMIT 25""",
        "sql_template": """WITH split AS (
    SELECT @year_start + CAST(FLOOR((@year_end - @year_start - 1) / 2.0) AS INT64) AS mid
),
company_apps AS (
    SELECT DISTINCT
        a.appln_id,
        CASE
            WHEN a.appln_filing_year <= (SELECT mid FROM split)
            THEN CONCAT(CAST(@year_start AS STRING), '–', CAST((SELECT mid FROM split) AS STRING))
            ELSE CONCAT(CAST((SELECT mid FROM split) + 1 AS STRING), '–', CAST(@year_end AS STRING))
        END AS period
    FROM tls201_appln a
    JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
    JOIN tls206_person p ON pa.person_id = p.person_id
    WHERE pa.applt_seq_nr > 0
      AND a.appln_filing_year BETWEEN @year_start AND @year_end
      AND (LOWER(p.person_name) LIKE CONCAT('%', LOWER(@company_name), '%')
           OR LOWER(p.han_name) LIKE CONCAT('%', LOWER(@company_name), '%'))
),
ipc_analysis AS (
    SELECT
        SUBSTR(ipc.ipc_class_symbol, 1, 4) AS ipc_main_class,
        ca.period,
        COUNT(DISTINCT ca.appln_id) AS applications
    FROM company_apps ca
    JOIN tls209_appln_ipc ipc ON ca.appln_id = ipc.appln_id
    GROUP BY SUBSTR(ipc.ipc_class_symbol, 1, 4), ca.period
),
top_classes AS (
    SELECT ipc_main_class, SUM(applications) AS total
    FROM ipc_analysis
    GROUP BY ipc_main_class
    ORDER BY total DESC
    LIMIT 20
)
SELECT
    ia.ipc_main_class,
    ia.period,
    ia.applications
FROM ipc_analysis ia
JOIN top_classes tc ON ia.ipc_main_class = tc.ipc_main_class
ORDER BY tc.total DESC, ia.period""",
    },

    "Q1F": {
        "title": "How successful are patent applications?",
        "tags": ["BUSINESS"],
        "series": "S1",
        "category": "Performance",
        "platforms": ["bigquery"],
        "description": "Grant rates and time-to-grant by patent office — prosecution success analysis",
        "explanation": """Analyzes patent prosecution success across different patent offices.
Uses publn_first_grant flag from tls211_pat_publn for reliable grant detection.
Time-to-grant = first grant publication date minus filing date.

Important caveats:
- Use filing years up to ~3 years before current year for meaningful grant rates
- Low grant rates at DPMA/UKIPO often reflect strategic priority filings
  (filed nationally first, then pursued via EP without seeking national grant)
- China (CNIPA) typically has the longest prosecution times""",
        "key_outputs": [
            "Grant rate percentage per office",
            "Average years to grant",
            "Median years to grant",
            "Total applications vs granted",
        ],
        "estimated_seconds_first_run": 12,
        "estimated_seconds_cached": 5,
        "visualization": {
            "x": "appln_auth",
            "y": "grant_rate_pct",
            "type": "bar",
        },
        "display_mode": None,
        "parameters": {
            "company_name": {
                "type": "text",
                "label": "Company Name",
                "defaults": "airbus",
                "placeholder": "e.g. airbus, boeing, siemens",
                "required": True,
            },
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2021,
                "required": True,
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": ["EP", "US", "CN", "FR", "DE", "JP", "KR", "GB"],
                "defaults": ["EP", "US", "CN", "FR", "DE", "JP", "KR"],
                "required": True,
            },
        },
        "sql": """WITH airbus_apps AS (
    SELECT DISTINCT
        a.appln_id,
        a.appln_auth,
        a.appln_filing_date,
        a.appln_filing_year,
        a.granted
    FROM tls201_appln a
    JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
    JOIN tls206_person p ON pa.person_id = p.person_id
    WHERE pa.applt_seq_nr > 0
      AND a.appln_filing_year BETWEEN 2014 AND 2021
      AND LOWER(p.person_name) LIKE '%airbus%'
      AND a.appln_auth IN ('EP', 'US', 'CN', 'FR', 'DE', 'JP', 'KR')
),
grant_info AS (
    SELECT
        aa.appln_id,
        aa.appln_auth,
        aa.appln_filing_date,
        aa.appln_filing_year,
        aa.granted,
        MIN(CASE WHEN pub.publn_first_grant = 'Y' THEN pub.publn_date END) AS grant_date
    FROM airbus_apps aa
    LEFT JOIN tls211_pat_publn pub ON aa.appln_id = pub.appln_id
    GROUP BY aa.appln_id, aa.appln_auth, aa.appln_filing_date, aa.appln_filing_year, aa.granted
)
SELECT
    appln_auth,
    COUNT(*) AS total_applications,
    COUNT(CASE WHEN granted = 'Y' THEN 1 END) AS granted,
    ROUND(COUNT(CASE WHEN granted = 'Y' THEN 1 END) * 100.0 / COUNT(*), 1) AS grant_rate_pct,
    ROUND(AVG(
        CASE WHEN grant_date IS NOT NULL AND grant_date > appln_filing_date
        THEN DATE_DIFF(grant_date, appln_filing_date, DAY) / 365.25
        END
    ), 1) AS avg_years_to_grant,
    ROUND(APPROX_QUANTILES(
        CASE WHEN grant_date IS NOT NULL AND grant_date > appln_filing_date
        THEN DATE_DIFF(grant_date, appln_filing_date, DAY) / 365.25
        END, 2)[OFFSET(1)], 1) AS median_years_to_grant
FROM grant_info
GROUP BY appln_auth
ORDER BY total_applications DESC""",
        "sql_template": """WITH company_apps AS (
    SELECT DISTINCT
        a.appln_id,
        a.appln_auth,
        a.appln_filing_date,
        a.appln_filing_year,
        a.granted
    FROM tls201_appln a
    JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
    JOIN tls206_person p ON pa.person_id = p.person_id
    WHERE pa.applt_seq_nr > 0
      AND a.appln_filing_year BETWEEN @year_start AND @year_end
      AND (LOWER(p.person_name) LIKE CONCAT('%', LOWER(@company_name), '%')
           OR LOWER(p.han_name) LIKE CONCAT('%', LOWER(@company_name), '%'))
      AND a.appln_auth IN UNNEST(@jurisdictions)
),
grant_info AS (
    SELECT
        ca.appln_id,
        ca.appln_auth,
        ca.appln_filing_date,
        ca.granted,
        MIN(CASE WHEN pub.publn_first_grant = 'Y' THEN pub.publn_date END) AS grant_date
    FROM company_apps ca
    LEFT JOIN tls211_pat_publn pub ON ca.appln_id = pub.appln_id
    GROUP BY ca.appln_id, ca.appln_auth, ca.appln_filing_date, ca.granted
)
SELECT
    appln_auth,
    COUNT(*) AS total_applications,
    COUNT(CASE WHEN granted = 'Y' THEN 1 END) AS granted,
    ROUND(COUNT(CASE WHEN granted = 'Y' THEN 1 END) * 100.0 / COUNT(*), 1) AS grant_rate_pct,
    ROUND(AVG(
        CASE WHEN grant_date IS NOT NULL AND grant_date > appln_filing_date
        THEN DATE_DIFF(grant_date, appln_filing_date, DAY) / 365.25
        END
    ), 1) AS avg_years_to_grant,
    ROUND(APPROX_QUANTILES(
        CASE WHEN grant_date IS NOT NULL AND grant_date > appln_filing_date
        THEN DATE_DIFF(grant_date, appln_filing_date, DAY) / 365.25
        END, 2)[OFFSET(1)], 1) AS median_years_to_grant
FROM grant_info
GROUP BY appln_auth
ORDER BY total_applications DESC""",
    },

    "Q1G": {
        "title": "Who are the R&D collaboration partners?",
        "tags": ["BUSINESS", "UNIVERSITY"],
        "series": "S1",
        "category": "Collaboration",
        "platforms": ["bigquery"],
        "description": "Co-applicants on joint patent applications — reveals strategic R&D partnerships",
        "explanation": """Identifies co-applicants on patents where the target company is also an applicant.
Only shows joint applications (nb_applicants > 1) and filters out the target company itself.

Co-application patterns reveal:
- Industry partnerships (suppliers, joint ventures)
- Research collaborations (universities, Fraunhofer, CNRS, DLR)
- Government agency cooperation (space agencies, defense)

The psn_sector field classifies partners as COMPANY, GOV NON-PROFIT, UNIVERSITY, etc.""",
        "key_outputs": [
            "Top co-applicants ranked by joint patents",
            "Partner sector classification",
            "Country of partner",
            "Duration of cooperation (first to last year)",
        ],
        "estimated_seconds_first_run": 15,
        "estimated_seconds_cached": 5,
        "visualization": {
            "x": "co_applicant",
            "y": "joint_applications",
            "type": "bar",
        },
        "display_mode": None,
        "parameters": {
            "company_name": {
                "type": "text",
                "label": "Company Name",
                "defaults": "airbus",
                "placeholder": "e.g. airbus, boeing, siemens",
                "required": True,
            },
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2024,
                "required": True,
            },
        },
        "sql": """WITH airbus_coapplications AS (
    SELECT DISTINCT
        a.appln_id,
        a.appln_filing_year,
        a.nb_applicants,
        p.person_name AS co_applicant,
        p.psn_sector AS co_sector,
        p.person_ctry_code AS co_country
    FROM tls201_appln a
    JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
    JOIN tls206_person p ON pa.person_id = p.person_id
    WHERE pa.applt_seq_nr > 0
      AND a.nb_applicants > 1
      AND a.appln_filing_year BETWEEN 2014 AND 2024
      AND NOT LOWER(p.person_name) LIKE '%airbus%'
      AND a.appln_id IN (
          SELECT pa2.appln_id
          FROM tls207_pers_appln pa2
          JOIN tls206_person p2 ON pa2.person_id = p2.person_id
          WHERE pa2.applt_seq_nr > 0
            AND LOWER(p2.person_name) LIKE '%airbus%'
      )
)
SELECT
    co_applicant,
    co_sector,
    co_country,
    COUNT(DISTINCT appln_id) AS joint_applications,
    MIN(appln_filing_year) AS first_cooperation,
    MAX(appln_filing_year) AS last_cooperation,
    COUNT(DISTINCT appln_filing_year) AS active_years
FROM airbus_coapplications
GROUP BY co_applicant, co_sector, co_country
HAVING COUNT(DISTINCT appln_id) >= 3
ORDER BY joint_applications DESC
LIMIT 30""",
        "sql_template": """WITH coapplications AS (
    SELECT DISTINCT
        a.appln_id,
        a.appln_filing_year,
        p.person_name AS co_applicant,
        p.psn_sector AS co_sector,
        p.person_ctry_code AS co_country
    FROM tls201_appln a
    JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
    JOIN tls206_person p ON pa.person_id = p.person_id
    WHERE pa.applt_seq_nr > 0
      AND a.nb_applicants > 1
      AND a.appln_filing_year BETWEEN @year_start AND @year_end
      AND NOT (LOWER(p.person_name) LIKE CONCAT('%', LOWER(@company_name), '%')
               OR LOWER(p.han_name) LIKE CONCAT('%', LOWER(@company_name), '%'))
      AND a.appln_id IN (
          SELECT pa2.appln_id
          FROM tls207_pers_appln pa2
          JOIN tls206_person p2 ON pa2.person_id = p2.person_id
          WHERE pa2.applt_seq_nr > 0
            AND (LOWER(p2.person_name) LIKE CONCAT('%', LOWER(@company_name), '%')
                 OR LOWER(p2.han_name) LIKE CONCAT('%', LOWER(@company_name), '%'))
      )
)
SELECT
    co_applicant,
    co_sector,
    co_country,
    COUNT(DISTINCT appln_id) AS joint_applications,
    MIN(appln_filing_year) AS first_cooperation,
    MAX(appln_filing_year) AS last_cooperation,
    COUNT(DISTINCT appln_filing_year) AS active_years
FROM coapplications
GROUP BY co_applicant, co_sector, co_country
HAVING COUNT(DISTINCT appln_id) >= 3
ORDER BY joint_applications DESC
LIMIT 30""",
    },

    "Q1H": {
        "title": "How broad is international patent protection?",
        "tags": ["BUSINESS"],
        "series": "S1",
        "category": "Trends",
        "platforms": ["bigquery"],
        "description": "Patent family size trends — indicator of international filing breadth and strategic value",
        "explanation": """Analyzes DOCDB family sizes over time. The family size indicates in how many
countries/offices an invention is protected. Larger families = higher strategic importance.

Only counts first filings (appln_id = earliest_filing_id) to avoid double-counting families.

Key metrics:
- Average family size trend (growing = broader protection strategy)
- Large families (10+) = high-value inventions filed worldwide
- Very large families (20+) = crown jewels of the portfolio""",
        "key_outputs": [
            "Unique patent families per year",
            "Average and median family size",
            "Count of large families (10+ and 20+ members)",
            "Percentage of large families",
        ],
        "estimated_seconds_first_run": 8,
        "estimated_seconds_cached": 3,
        "visualization": {
            "x": "appln_filing_year",
            "y": "avg_family_size",
            "type": "line",
        },
        "display_mode": None,
        "parameters": {
            "company_name": {
                "type": "text",
                "label": "Company Name",
                "defaults": "airbus",
                "placeholder": "e.g. airbus, boeing, siemens",
                "required": True,
            },
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2024,
                "required": True,
            },
        },
        "sql": """WITH airbus_families AS (
    SELECT DISTINCT
        a.docdb_family_id,
        a.appln_filing_year,
        a.docdb_family_size
    FROM tls201_appln a
    JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
    JOIN tls206_person p ON pa.person_id = p.person_id
    WHERE pa.applt_seq_nr > 0
      AND a.appln_filing_year BETWEEN 2014 AND 2024
      AND LOWER(p.person_name) LIKE '%airbus%'
      AND a.docdb_family_id > 0
      AND a.appln_id = a.earliest_filing_id
)
SELECT
    appln_filing_year,
    COUNT(DISTINCT docdb_family_id) AS unique_families,
    ROUND(AVG(docdb_family_size), 1) AS avg_family_size,
    ROUND(APPROX_QUANTILES(docdb_family_size, 2)[OFFSET(1)], 0) AS median_family_size,
    MAX(docdb_family_size) AS max_family_size,
    COUNT(CASE WHEN docdb_family_size >= 10 THEN 1 END) AS large_families_10plus,
    COUNT(CASE WHEN docdb_family_size >= 20 THEN 1 END) AS very_large_families_20plus,
    ROUND(COUNT(CASE WHEN docdb_family_size >= 10 THEN 1 END) * 100.0 /
          COUNT(DISTINCT docdb_family_id), 1) AS pct_large_families
FROM airbus_families
GROUP BY appln_filing_year
ORDER BY appln_filing_year""",
        "sql_template": """WITH company_families AS (
    SELECT DISTINCT
        a.docdb_family_id,
        a.appln_filing_year,
        a.docdb_family_size
    FROM tls201_appln a
    JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
    JOIN tls206_person p ON pa.person_id = p.person_id
    WHERE pa.applt_seq_nr > 0
      AND a.appln_filing_year BETWEEN @year_start AND @year_end
      AND (LOWER(p.person_name) LIKE CONCAT('%', LOWER(@company_name), '%')
           OR LOWER(p.han_name) LIKE CONCAT('%', LOWER(@company_name), '%'))
      AND a.docdb_family_id > 0
      AND a.appln_id = a.earliest_filing_id
)
SELECT
    appln_filing_year,
    COUNT(DISTINCT docdb_family_id) AS unique_families,
    ROUND(AVG(docdb_family_size), 1) AS avg_family_size,
    ROUND(APPROX_QUANTILES(docdb_family_size, 2)[OFFSET(1)], 0) AS median_family_size,
    MAX(docdb_family_size) AS max_family_size,
    COUNT(CASE WHEN docdb_family_size >= 10 THEN 1 END) AS large_families_10plus,
    COUNT(CASE WHEN docdb_family_size >= 20 THEN 1 END) AS very_large_families_20plus,
    ROUND(COUNT(CASE WHEN docdb_family_size >= 10 THEN 1 END) * 100.0 /
          COUNT(DISTINCT docdb_family_id), 1) AS pct_large_families
FROM company_families
GROUP BY appln_filing_year
ORDER BY appln_filing_year""",
    },

    "Q1I": {
        "title": "What future technologies are emerging?",
        "tags": ["BUSINESS", "UNIVERSITY"],
        "series": "S1",
        "category": "Technology",
        "platforms": ["bigquery"],
        "description": "Future technology patent trends — Hydrogen, E-Propulsion, AI, UAV, Additive Manufacturing",
        "explanation": """Identifies patents in five key future technology areas using CPC classifications
and English title keywords. Tracks annual filing activity per technology.

Technology categories (aerospace-focused but broadly applicable):
- Hydrogen/Fuel Cells: CPC Y02E 60/5, H01M 8, C01B 3 + title keywords
- Electric/Hybrid Propulsion: CPC B64D 27/24, H02K + title keywords
- Artificial Intelligence: CPC G06N + title keywords (machine learning, neural network)
- UAV/Drones/Urban Air Mobility: title keywords (unmanned, UAV, drone, eVTOL)
- Additive Manufacturing: CPC B33Y + title keywords (3D print)
- Sustainable Transport: CPC Y02T

Requires English titles (tls202_appln_title with appln_title_lg = 'en').""",
        "key_outputs": [
            "Annual application count per future tech area",
            "Technology trend lines over time",
            "Emerging vs declining technology areas",
        ],
        "estimated_seconds_first_run": 15,
        "estimated_seconds_cached": 5,
        "visualization": {
            "x": "appln_filing_year",
            "y": "applications",
            "color": "future_tech_area",
            "type": "line",
        },
        "display_mode": None,
        "parameters": {
            "company_name": {
                "type": "text",
                "label": "Company Name",
                "defaults": "airbus",
                "placeholder": "e.g. airbus, boeing, siemens",
                "required": True,
            },
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2024,
                "required": True,
            },
        },
        "sql": """WITH airbus_apps AS (
    SELECT DISTINCT
        a.appln_id,
        a.appln_filing_year,
        a.docdb_family_id
    FROM tls201_appln a
    JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
    JOIN tls206_person p ON pa.person_id = p.person_id
    WHERE pa.applt_seq_nr > 0
      AND a.appln_filing_year BETWEEN 2014 AND 2024
      AND LOWER(p.person_name) LIKE '%airbus%'
),
future_tech AS (
    SELECT
        aa.appln_id,
        aa.appln_filing_year,
        CASE
            WHEN cpc.cpc_class_symbol LIKE 'Y02E%60/5%'
              OR cpc.cpc_class_symbol LIKE 'H01M%8/%'
              OR cpc.cpc_class_symbol LIKE 'C01B%3/%'
              OR LOWER(t.appln_title) LIKE '%hydrogen%'
              OR LOWER(t.appln_title) LIKE '%fuel cell%'
            THEN 'Hydrogen/Fuel Cells'
            WHEN cpc.cpc_class_symbol LIKE 'B64D%27/24%'
              OR cpc.cpc_class_symbol LIKE 'H02K%'
              OR (LOWER(t.appln_title) LIKE '%electric%' AND LOWER(t.appln_title) LIKE '%propuls%')
              OR LOWER(t.appln_title) LIKE '%hybrid%propuls%'
            THEN 'Electric/Hybrid Propulsion'
            WHEN cpc.cpc_class_symbol LIKE 'G06N%'
              OR LOWER(t.appln_title) LIKE '%machine learning%'
              OR LOWER(t.appln_title) LIKE '%neural network%'
              OR LOWER(t.appln_title) LIKE '%deep learning%'
              OR LOWER(t.appln_title) LIKE '%artificial intell%'
            THEN 'Artificial Intelligence'
            WHEN LOWER(t.appln_title) LIKE '%unmanned%'
              OR LOWER(t.appln_title) LIKE '%uav%'
              OR LOWER(t.appln_title) LIKE '%drone%'
              OR LOWER(t.appln_title) LIKE '%urban air mobil%'
              OR LOWER(t.appln_title) LIKE '%evtol%'
            THEN 'UAV/Drones/UAM'
            WHEN cpc.cpc_class_symbol LIKE 'B33Y%'
              OR LOWER(t.appln_title) LIKE '%additive manufactur%'
              OR LOWER(t.appln_title) LIKE '%3d print%'
            THEN 'Additive Manufacturing'
            WHEN cpc.cpc_class_symbol LIKE 'Y02T%'
            THEN 'Sustainable Transport (Y02T)'
        END AS future_tech_area
    FROM airbus_apps aa
    LEFT JOIN tls224_appln_cpc cpc ON aa.appln_id = cpc.appln_id
    LEFT JOIN tls202_appln_title t ON aa.appln_id = t.appln_id
    WHERE t.appln_title_lg = 'en'
)
SELECT
    future_tech_area,
    appln_filing_year,
    COUNT(DISTINCT appln_id) AS applications
FROM future_tech
WHERE future_tech_area IS NOT NULL
GROUP BY future_tech_area, appln_filing_year
ORDER BY future_tech_area, appln_filing_year""",
        "sql_template": """WITH company_apps AS (
    SELECT DISTINCT
        a.appln_id,
        a.appln_filing_year
    FROM tls201_appln a
    JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
    JOIN tls206_person p ON pa.person_id = p.person_id
    WHERE pa.applt_seq_nr > 0
      AND a.appln_filing_year BETWEEN @year_start AND @year_end
      AND (LOWER(p.person_name) LIKE CONCAT('%', LOWER(@company_name), '%')
           OR LOWER(p.han_name) LIKE CONCAT('%', LOWER(@company_name), '%'))
),
future_tech AS (
    SELECT
        ca.appln_id,
        ca.appln_filing_year,
        CASE
            WHEN cpc.cpc_class_symbol LIKE 'Y02E%60/5%'
              OR cpc.cpc_class_symbol LIKE 'H01M%8/%'
              OR cpc.cpc_class_symbol LIKE 'C01B%3/%'
              OR LOWER(t.appln_title) LIKE '%hydrogen%'
              OR LOWER(t.appln_title) LIKE '%fuel cell%'
            THEN 'Hydrogen/Fuel Cells'
            WHEN cpc.cpc_class_symbol LIKE 'B64D%27/24%'
              OR cpc.cpc_class_symbol LIKE 'H02K%'
              OR (LOWER(t.appln_title) LIKE '%electric%' AND LOWER(t.appln_title) LIKE '%propuls%')
              OR LOWER(t.appln_title) LIKE '%hybrid%propuls%'
            THEN 'Electric/Hybrid Propulsion'
            WHEN cpc.cpc_class_symbol LIKE 'G06N%'
              OR LOWER(t.appln_title) LIKE '%machine learning%'
              OR LOWER(t.appln_title) LIKE '%neural network%'
              OR LOWER(t.appln_title) LIKE '%deep learning%'
              OR LOWER(t.appln_title) LIKE '%artificial intell%'
            THEN 'Artificial Intelligence'
            WHEN LOWER(t.appln_title) LIKE '%unmanned%'
              OR LOWER(t.appln_title) LIKE '%uav%'
              OR LOWER(t.appln_title) LIKE '%drone%'
              OR LOWER(t.appln_title) LIKE '%urban air mobil%'
              OR LOWER(t.appln_title) LIKE '%evtol%'
            THEN 'UAV/Drones/UAM'
            WHEN cpc.cpc_class_symbol LIKE 'B33Y%'
              OR LOWER(t.appln_title) LIKE '%additive manufactur%'
              OR LOWER(t.appln_title) LIKE '%3d print%'
            THEN 'Additive Manufacturing'
            WHEN cpc.cpc_class_symbol LIKE 'Y02T%'
            THEN 'Sustainable Transport (Y02T)'
        END AS future_tech_area
    FROM company_apps ca
    LEFT JOIN tls224_appln_cpc cpc ON ca.appln_id = cpc.appln_id
    LEFT JOIN tls202_appln_title t ON ca.appln_id = t.appln_id
    WHERE t.appln_title_lg = 'en'
)
SELECT
    future_tech_area,
    appln_filing_year,
    COUNT(DISTINCT appln_id) AS applications
FROM future_tech
WHERE future_tech_area IS NOT NULL
GROUP BY future_tech_area, appln_filing_year
ORDER BY future_tech_area, appln_filing_year""",
    },

    "Q1J": {
        "title": "Where are the inventors located?",
        "tags": ["PATLIB", "UNIVERSITY"],
        "series": "S1",
        "category": "Regional",
        "platforms": ["bigquery"],
        "description": "Inventor locations by NUTS region — shows where R&D physically takes place",
        "explanation": """Maps inventor addresses to NUTS Level 2 regions to identify innovation hotspots.
Uses invt_seq_nr > 0 (inventors only, not applicants) on patents where the target company is applicant.

NUTS (Nomenclature of Territorial Units for Statistics) regions identify:
- Manufacturing sites (e.g. Hamburg for Airbus final assembly)
- R&D centers (e.g. Toulouse for Airbus design)
- Supplier clusters and university partnerships

Requires at least 10 patents per region for inclusion.""",
        "key_outputs": [
            "Top inventor regions by patent count",
            "Unique inventor count per region",
            "Country distribution of R&D activity",
        ],
        "estimated_seconds_first_run": 12,
        "estimated_seconds_cached": 5,
        "visualization": {
            "x": "region_name",
            "y": "applications",
            "type": "bar",
        },
        "display_mode": None,
        "parameters": {
            "company_name": {
                "type": "text",
                "label": "Company Name",
                "defaults": "airbus",
                "placeholder": "e.g. airbus, boeing, siemens",
                "required": True,
            },
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2024,
                "required": True,
            },
        },
        "sql": """SELECT
    p.person_ctry_code AS inventor_country,
    SUBSTR(p.nuts, 1, 4) AS nuts_region,
    n.nuts_label AS region_name,
    COUNT(DISTINCT a.appln_id) AS applications,
    COUNT(DISTINCT p.person_id) AS unique_inventors
FROM tls201_appln a
JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
JOIN tls206_person p ON pa.person_id = p.person_id
LEFT JOIN tls904_nuts n ON SUBSTR(p.nuts, 1, 4) = n.nuts
WHERE pa.invt_seq_nr > 0
  AND a.appln_filing_year BETWEEN 2014 AND 2024
  AND a.appln_id IN (
      SELECT pa2.appln_id
      FROM tls207_pers_appln pa2
      JOIN tls206_person p2 ON pa2.person_id = p2.person_id
      WHERE pa2.applt_seq_nr > 0
        AND LOWER(p2.person_name) LIKE '%airbus%'
  )
  AND p.nuts IS NOT NULL
  AND LENGTH(p.nuts) >= 4
GROUP BY p.person_ctry_code, SUBSTR(p.nuts, 1, 4), n.nuts_label
HAVING COUNT(DISTINCT a.appln_id) >= 10
ORDER BY applications DESC""",
        "sql_template": """SELECT
    p.person_ctry_code AS inventor_country,
    SUBSTR(p.nuts, 1, 4) AS nuts_region,
    n.nuts_label AS region_name,
    COUNT(DISTINCT a.appln_id) AS applications,
    COUNT(DISTINCT p.person_id) AS unique_inventors
FROM tls201_appln a
JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
JOIN tls206_person p ON pa.person_id = p.person_id
LEFT JOIN tls904_nuts n ON SUBSTR(p.nuts, 1, 4) = n.nuts
WHERE pa.invt_seq_nr > 0
  AND a.appln_filing_year BETWEEN @year_start AND @year_end
  AND a.appln_id IN (
      SELECT pa2.appln_id
      FROM tls207_pers_appln pa2
      JOIN tls206_person p2 ON pa2.person_id = p2.person_id
      WHERE pa2.applt_seq_nr > 0
        AND (LOWER(p2.person_name) LIKE CONCAT('%', LOWER(@company_name), '%')
             OR LOWER(p2.han_name) LIKE CONCAT('%', LOWER(@company_name), '%'))
  )
  AND p.nuts IS NOT NULL
  AND LENGTH(p.nuts) >= 4
GROUP BY p.person_ctry_code, SUBSTR(p.nuts, 1, 4), n.nuts_label
HAVING COUNT(DISTINCT a.appln_id) >= 10
ORDER BY applications DESC""",
    },
}
