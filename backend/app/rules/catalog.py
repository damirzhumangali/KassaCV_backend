import json
from pathlib import Path
from typing import Any


REQUIRED = {"rule_id", "type", "visual_signs", "not_a_violation", "source", "clause", "source_url", "interpretation", "verified_by", "verified_at"}


def load_catalog(path: Path) -> dict[str, dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Cannot load rules catalog: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("rules"), list):
        raise RuntimeError("Rules catalog must contain a rules array")
    catalog: dict[str, dict[str, Any]] = {}
    for rule in data["rules"]:
        if not isinstance(rule, dict) or not REQUIRED.issubset(rule):
            raise RuntimeError("Each rule must contain all required catalog fields")
        if rule["rule_id"] in catalog:
            raise RuntimeError(f"Duplicate rule_id: {rule['rule_id']}")
        if not all(isinstance(rule[key], str) and rule[key].strip() for key in REQUIRED):
            raise RuntimeError(f"Rule {rule['rule_id']} contains an empty or invalid field")
        catalog[rule["rule_id"]] = rule
    return catalog
