from pathlib import Path
import pytest
from app.rules.catalog import load_catalog


def test_load_catalog_valid():
    catalog_path = Path(__file__).parent.parent / "app" / "rules" / "rules_catalog.json"
    catalog = load_catalog(catalog_path)
    assert len(catalog) > 0
    for rule_id, rule in catalog.items():
        assert "rule_id" in rule
        assert "type" in rule
        assert "source" in rule
        assert "clause" in rule
        assert "interpretation" in rule
        assert rule["source_url"].startswith("http")
