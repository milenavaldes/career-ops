#!/usr/bin/env python3
"""Validate Freehire search responses, not just HTTP connectivity."""
import datetime
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://freehire.me/api/v1/jobs/search"
OUT = Path("freehire-results")
OUT.mkdir(exist_ok=True)
queries = ["Senior SDET", "AI Developer Tools"]
summary = []
failed = False

for i, query in enumerate(queries, 1):
    params = {"q": query, "work_mode": "remote", "countries": "US", "limit": 100}
    url = BASE + "?" + urllib.parse.urlencode(params)
    record = {"query": query, "url": url, "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "career-ops-freehire-smoke-test/1.1"})
        with urllib.request.urlopen(req, timeout=30) as response:
            record["http_status"] = response.status
            payload = json.loads(response.read(5_000_000))
        (OUT / f"query-{i}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False))
        if not isinstance(payload, dict) or not isinstance(payload.get("meta"), dict):
            raise ValueError("Missing expected meta object")
        meta = payload["meta"]
        record["ignored_params"] = meta.get("ignored_params")
        record["total"] = meta.get("total")
        data = payload.get("data")
        if isinstance(data, list):
            record["items_count"] = len(data)
        elif isinstance(data, dict):
            record["items_count"] = len(data.get("jobs", [])) if isinstance(data.get("jobs"), list) else None
        else:
            record["items_count"] = None
        if record["ignored_params"]:
            raise ValueError(f"API ignored filters: {record['ignored_params']}")
        if record["total"] is None or record["items_count"] is None:
            raise ValueError("Unrecognized search response structure; inspect saved JSON")
    except Exception as exc:
        failed = True
        record["error"] = str(exc)
    summary.append(record)
    print(json.dumps(record, ensure_ascii=False), flush=True)
    time.sleep(1)

(OUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
if failed:
    raise SystemExit("Freehire search smoke test failed; inspect artifact")
