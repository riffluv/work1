#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
ASSET_BUILDER = ROOT_DIR / "scripts/build-coconala-temperature-assets.py"
PREFERRED_PATH = ROOT_DIR / "ops/tests/temperature-assets/preferred/quality-audit-preferred.jsonl"
PAIR_BUILDER = ROOT_DIR / "scripts/build-coconala-temperature-pairs.py"
RERANKER_EXPORTER = ROOT_DIR / "scripts/export-coconala-temperature-reranker-set.py"


def load_asset_builder():
    spec = importlib.util.spec_from_file_location("build_coconala_temperature_assets", ASSET_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load asset builder: {ASSET_BUILDER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_jsonl_index(path: Path, key_name: str) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    if not path.exists():
        return rows
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        row = json.loads(line)
        key = row.get(key_name)
        if key:
            rows[key] = row
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Import preferred rewrites from one external quality-audit report.")
    parser.add_argument("--report", required=True)
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--refresh-assets", action="store_true")
    args = parser.parse_args()

    builder = load_asset_builder()
    report_path = Path(args.report)
    rows = builder.extract_quality_audit_preferred([report_path])
    if args.case_id:
        wanted = set(args.case_id)
        rows = [row for row in rows if row.get("case_id") in wanted]

    if not rows:
        raise SystemExit("no preferred rows extracted from report")

    preferred_index = load_jsonl_index(PREFERRED_PATH, "case_id")
    for row in rows:
        preferred_index[row["case_id"]] = row

    write_jsonl(PREFERRED_PATH, [preferred_index[key] for key in sorted(preferred_index)])
    print(PREFERRED_PATH)

    if args.refresh_assets:
        subprocess.run(["python3", str(PAIR_BUILDER), "--save-report"], check=True)
        subprocess.run(["python3", str(RERANKER_EXPORTER), "--save-report"], check=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
