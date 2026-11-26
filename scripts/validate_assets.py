#!/usr/bin/env python3
"""Validate registry paths, metadata, unique IDs, and documented license families."""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'assets/manifest.json').read_text())
license_text=(ROOT/'assets/LICENSES.md').read_text()
required=('id','name','category','subcategory','tags','mood','style','description','path','format','dimensions','recolorable','license','source')
errors=[]; ids=set()
for i,item in enumerate(manifest.get('assets',[])):
    for key in required:
        if key not in item or item[key] is None or item[key]=='' : errors.append(f'entry {i}: missing {key}')
    if item.get('id') in ids: errors.append(f'duplicate ID: {item.get("id")}')
    ids.add(item.get('id'))
    target=ROOT/item.get('path','')
    if not target.is_file(): errors.append(f'{item.get("id")}: missing path {item.get("path")}')
    if item.get('license') not in license_text: errors.append(f'{item.get("id")}: license {item.get("license")} absent from LICENSES.md')
    if not isinstance(item.get('tags'),list) or not item.get('tags'): errors.append(f'{item.get("id")}: tags must be a non-empty list')
if errors:
    print('\n'.join(errors[:100])); print(f'FAIL: {len(errors)} issue(s) across {len(ids)} IDs'); sys.exit(1)
print(f'PASS: {len(ids)} unique assets; all paths, required metadata, and license-family entries are valid.')
for category,count in sorted(Counter(x['category'] for x in manifest['assets']).items()): print(f'{category}: {count}')
