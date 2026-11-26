"""Local asset registry querying. Registry paths are repository-relative and never executed."""
from __future__ import annotations
import json, re
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "assets" / "manifest.json"

@lru_cache(maxsize=1)
def _registry() -> list[dict[str, Any]]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))["assets"]

def list_categories() -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for row in _registry(): counts[row["category"]] = counts.get(row["category"], 0) + 1
    return [{"name": name, "count": counts[name]} for name in sorted(counts)]

def get_asset(asset_id: str) -> dict[str, Any] | None:
    return next((row for row in _registry() if row["id"] == asset_id), None)

def search_assets(query: str = "", category: str | None = None, tags: list[str] | None = None,
                  mood: str | None = None, limit: int = 30, offset: int = 0) -> list[dict[str, Any]]:
    words = set(re.findall(r"[a-z0-9]+", query.lower()))
    wanted = {tag.lower() for tag in (tags or [])}
    results = []
    for row in _registry():
        if category and row["category"] != category: continue
        if mood and mood.lower() not in {m.lower() for m in row.get("mood", [])}: continue
        row_tags = {str(x).lower() for x in row.get("tags", [])}
        haystack = " ".join([row.get("name", ""), row.get("subcategory", ""), row.get("description", ""), *row_tags]).lower()
        if wanted and not wanted.issubset(row_tags): continue
        overlap = sum(1 for word in words if word in haystack)
        if words and overlap == 0: continue
        results.append((overlap, row))
    results.sort(key=lambda pair: (-pair[0], pair[1]["category"], pair[1]["name"]))
    start=max(0,offset)
    return [row for _, row in results[start:start+max(1, min(limit, 2000))]]
