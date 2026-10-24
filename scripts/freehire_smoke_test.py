#!/usr/bin/env python3
"""Isolated Freehire API smoke test; no credentials or resume required."""
import json, os, time, urllib.parse, urllib.request, urllib.error
from pathlib import Path

BASE = "https://freehire.me/api/v1/jobs"
OUT = Path("freehire-results")
OUT.mkdir(exist_ok=True)
queries = ["Senior SDET", "AI Developer Tools"]
summary = []
for i, query in enumerate(queries):
    params = urllib.parse.urlencode({"q": query})
    url = BASE + "?" + params
    record = {"query": query, "url": url, "timestamp_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()}
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "career-ops-freehire-smoke-test/1.0"})
        with urllib.request.urlopen(req, timeout=25) as response:
            body = response.read(2_000_000)
            record["http_status"] = response.status
            record["content_type"] = response.headers.get("Content-Type")
            try:
                data = json.loads(body)
                (OUT / f"query-{i+1}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))
                record["json_type"] = type(data).__name__
                record["top_level_keys"] = list(data.keys()) if isinstance(data, dict) else None
                record["items_count"] = len(data) if isinstance(data, list) else None
            except ValueError:
                record["error"] = "Response is not valid JSON"
                record["body_preview"] = body[:500].decode("utf-8", "replace")
    except Exception as e:
        record["error"] = str(e)
    summary.append(record)
    print(json.dumps(record, ensure_ascii=False), flush=True)
    time.sleep(1)
(OUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
