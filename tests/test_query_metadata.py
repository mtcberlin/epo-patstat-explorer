"""Tests for Story 2-2: Query Metadata Display functionality."""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from queries_bq import QUERIES, STAKEHOLDERS, SERIES


class TestQueryMetadataStructure:
    """Tests for query metadata completeness (AC #1, #3)."""

    def test_all_queries_have_title(self):
        """Every query has a title."""
        for qid, query in QUERIES.items():
            assert 'title' in query, f"{qid} missing title"
            assert query['title'], f"{qid} has empty title"

    def test_all_queries_have_description(self):
        """Every query has a description."""
        for qid, query in QUERIES.items():
            assert 'description' in query, f"{qid} missing description"
            assert query['description'], f"{qid} has empty description"

    def test_all_queries_have_tags(self):
        """Every query has stakeholder tags."""
        for qid, query in QUERIES.items():
            assert 'tags' in query, f"{qid} missing tags"
            assert len(query['tags']) > 0, f"{qid} has no tags"

    def test_all_queries_have_category(self):
        """Every query has a category."""
        valid_categories = ["Overview", "Trends", "Regional", "Technology", "Performance", "Collaboration"]
        for qid, query in QUERIES.items():
            assert 'category' in query, f"{qid} missing category"
            assert query['category'] in valid_categories, f"{qid} has invalid category: {query['category']}"

    def test_all_queries_have_platforms(self):
        """Every query has a platforms field with valid values."""
        valid_platforms = {"bigquery", "tip"}
        for qid, query in QUERIES.items():
            assert 'platforms' in query, f"{qid} missing platforms"
            assert isinstance(query['platforms'], list), f"{qid} platforms is not a list"
            assert len(query['platforms']) > 0, f"{qid} has empty platforms"
            for p in query['platforms']:
                assert p in valid_platforms, f"{qid} has invalid platform: {p}"

    def test_all_queries_have_estimated_time(self):
        """Every query has estimated execution time."""
        for qid, query in QUERIES.items():
            assert 'estimated_seconds_cached' in query, f"{qid} missing estimated_seconds_cached"
            assert query['estimated_seconds_cached'] > 0, f"{qid} has invalid estimated time"

    def test_all_queries_have_sql(self):
        """Every query has SQL."""
        for qid, query in QUERIES.items():
            assert 'sql' in query, f"{qid} missing sql"
            assert query['sql'].strip(), f"{qid} has empty sql"

    def test_all_tags_are_valid_stakeholders(self):
        """All query tags are valid stakeholder types."""
        valid_stakeholders = set(STAKEHOLDERS.keys())
        for qid, query in QUERIES.items():
            for tag in query.get('tags', []):
                assert tag in valid_stakeholders, f"{qid} has invalid tag: {tag}"


class TestQueryTitles:
    """Tests for question-style titles (AC #1)."""

    def test_titles_are_questions_or_descriptive(self):
        """Titles should be question-style or descriptive statements."""
        for qid, query in QUERIES.items():
            title = query.get('title', '')
            # Titles should either end with ? or be descriptive
            # At minimum, they should be meaningful (>10 chars)
            assert len(title) > 10, f"{qid} title too short: {title}"


class TestQueryExplanations:
    """Tests for query explanations (AC #2)."""

    def test_queries_have_explanations(self):
        """Most queries should have explanations."""
        queries_with_explanations = sum(1 for q in QUERIES.values() if q.get('explanation'))
        total_queries = len(QUERIES)
        # At least 80% should have explanations
        assert queries_with_explanations >= total_queries * 0.8


class TestStakeholderDefinitions:
    """Tests for stakeholder definitions."""

    def test_stakeholders_defined(self):
        """STAKEHOLDERS dict is defined with descriptions."""
        assert STAKEHOLDERS is not None
        assert len(STAKEHOLDERS) == 3

    def test_stakeholder_has_descriptions(self):
        """Each stakeholder has a description."""
        assert STAKEHOLDERS["PATLIB"]
        assert STAKEHOLDERS["BUSINESS"]
        assert STAKEHOLDERS["UNIVERSITY"]


class TestQueryCount:
    """Tests for query library size."""

    def test_minimum_query_count(self):
        """Library has minimum required queries (10 per series)."""
        assert len(QUERIES) >= 10

    def test_queries_across_categories(self):
        """Queries are distributed across categories."""
        categories = {}
        for query in QUERIES.values():
            cat = query.get('category', 'Unknown')
            categories[cat] = categories.get(cat, 0) + 1

        # Each category should have at least 1 query
        for cat, count in categories.items():
            assert count >= 1, f"Category {cat} has only {count} queries"


class TestQueryParameters:
    """Tests for Story 1.8: Query-specific parameter system."""

    def test_all_queries_have_parameters_key(self):
        """Every query has a 'parameters' key (AC #1)."""
        for qid, query in QUERIES.items():
            assert 'parameters' in query, f"{qid} missing 'parameters' key"

    def test_parameters_is_dict(self):
        """Parameters must be a dict."""
        for qid, query in QUERIES.items():
            assert isinstance(query.get('parameters'), dict), f"{qid} parameters is not a dict"

    def test_parameter_types_are_valid(self):
        """All parameter types are valid (AC #1)."""
        valid_types = {'year_range', 'multiselect', 'select', 'text'}
        for qid, query in QUERIES.items():
            for param_name, param_config in query.get('parameters', {}).items():
                param_type = param_config.get('type')
                assert param_type in valid_types, \
                    f"{qid}.{param_name} has invalid type: {param_type}"

    def test_year_range_has_defaults(self):
        """year_range parameters have default_start and default_end."""
        for qid, query in QUERIES.items():
            for param_name, param_config in query.get('parameters', {}).items():
                if param_config.get('type') == 'year_range':
                    assert 'default_start' in param_config, \
                        f"{qid}.{param_name} missing default_start"
                    assert 'default_end' in param_config, \
                        f"{qid}.{param_name} missing default_end"

    def test_multiselect_has_options(self):
        """multiselect parameters have options defined."""
        for qid, query in QUERIES.items():
            for param_name, param_config in query.get('parameters', {}).items():
                if param_config.get('type') == 'multiselect':
                    options = param_config.get('options')
                    assert options is not None, \
                        f"{qid}.{param_name} missing options"
                    # Options can be a list or a reference string
                    valid_refs = {'jurisdictions', 'wipo_fields', 'tech_sectors', 'medtech_competitors'}
                    assert isinstance(options, list) or options in valid_refs, \
                        f"{qid}.{param_name} has invalid options: {options}"

    def test_select_has_options(self):
        """select parameters have options defined."""
        for qid, query in QUERIES.items():
            for param_name, param_config in query.get('parameters', {}).items():
                if param_config.get('type') == 'select':
                    options = param_config.get('options')
                    assert options is not None, \
                        f"{qid}.{param_name} missing options"
                    # Options can be a list or a reference string
                    valid_refs = {'jurisdictions', 'wipo_fields', 'tech_sectors', 'medtech_competitors'}
                    assert isinstance(options, list) or options in valid_refs, \
                        f"{qid}.{param_name} has invalid options: {options}"

    def test_parameters_match_sql_template(self):
        """Queries with parameters must use them in sql_template (AC #4)."""
        for qid, query in QUERIES.items():
            params = query.get('parameters', {})
            sql_template = query.get('sql_template', '')

            if 'year_range' in params:
                assert '@year_start' in sql_template or '@year_end' in sql_template, \
                    f"{qid} has year_range param but sql_template doesn't use it"

            if 'jurisdictions' in params:
                assert '@jurisdictions' in sql_template, \
                    f"{qid} has jurisdictions param but sql_template doesn't use it"

            if 'tech_sector' in params:
                assert '@tech_sector' in sql_template, \
                    f"{qid} has tech_sector param but sql_template doesn't use it"

            if 'company_name' in params:
                assert '@company_name' in sql_template, \
                    f"{qid} has company_name param but sql_template doesn't use it"

    def test_parameter_count_reasonable(self):
        """Each query has 0-4 parameters typically (AC #5)."""
        for qid, query in QUERIES.items():
            param_count = len(query.get('parameters', {}))
            assert param_count <= 5, \
                f"{qid} has {param_count} parameters (typically 0-4)"


class TestQuerySeries:
    """Tests for series-based query grouping."""

    def test_all_queries_have_series(self):
        """Every query belongs to a series."""
        for qid, query in QUERIES.items():
            assert 'series' in query, f"{qid} missing 'series' key"
            assert query['series'] in SERIES, f"{qid} has invalid series: {query['series']}"

    def test_series_have_required_fields(self):
        """Every series has required metadata."""
        for sid, series in SERIES.items():
            assert 'title' in series, f"Series {sid} missing title"
            assert 'description' in series, f"Series {sid} missing description"

    def test_s1_has_10_queries(self):
        """Series S1 (Company Filing Strategy) has 10 queries."""
        s1_queries = [q for q in QUERIES.values() if q.get('series') == 'S1']
        assert len(s1_queries) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
