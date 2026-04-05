#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT_DIR / "ops/tests/stock/inbox/stock-bulk-100.txt"
OUT_DIR = ROOT_DIR / "ops/tests/stock"


def parse_blocks(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    blocks = [block.strip() for block in text.split("----") if "case_id:" in block]
    parsed: list[dict] = []
    for block in blocks:
        item: dict[str, str] = {"__raw__": block}
        for raw_line in block.splitlines():
            if ":" not in raw_line:
                continue
            key, value = raw_line.split(":", 1)
            item[key.strip()] = value.strip()
        parsed.append(item)
    return parsed


def classify_bucket(case: dict) -> str:
    state = case.get("state", "")
    raw = case.get("raw_message", "")
    note = case.get("note", "")
    service_hint = case.get("service_hint", "")
    combined = f"{raw}\n{note}"

    edge_markers = [
        "STRIPE_SECRET_KEY",
        "パスワード",
        "ログイン情報",
        "直接やってもら",
        "Zoom",
        "通話",
        "本番",
        "個人情報が見えてる",
        "不正アクセス",
        "二重に引き落と",
    ]
    holdout_markers = [
        "どちらに当てはまるか",
        "整理が必要かもしれない",
        "修正だけお願いしたい",
        "25,000円",
        "値引",
        "安く",
        "複数件まとめて",
        "価値があった",
        "評価",
        "別なんですが",
        "同じ方に頼みたい",
    ]

    if any(marker in combined for marker in edge_markers):
        return "edge"
    if service_hint == "boundary":
        return "holdout"
    if state in {"delivered", "closed"}:
        return "holdout"
    if any(marker in combined for marker in holdout_markers):
        return "holdout"
    return "eval"


def write_bucket(path: Path, cases: list[dict]) -> None:
    lines = [
        f"# generated from {DEFAULT_INPUT.name}",
        f"# bucket: {path.stem}",
        "",
    ]
    for case in cases:
        lines.append("----")
        lines.append("")
        lines.extend(case["__raw__"].splitlines())
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Split a stock batch into eval / holdout / edge files.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--prefix", default="stock-bulk-100")
    args = parser.parse_args()

    source_path = Path(args.input)
    cases = parse_blocks(source_path)
    buckets: dict[str, list[dict]] = defaultdict(list)
    for case in cases:
        bucket = classify_bucket(case)
        buckets[bucket].append(case)

    seed_cases = cases[:10]
    write_bucket(OUT_DIR / "seed" / f"{args.prefix}-seed.txt", seed_cases)
    for bucket in ["eval", "holdout", "edge"]:
        write_bucket(OUT_DIR / bucket / f"{args.prefix}-{bucket}.txt", buckets.get(bucket, []))

    print(
        "seed={seed} eval={eval} holdout={holdout} edge={edge}".format(
            seed=len(seed_cases),
            eval=len(buckets.get("eval", [])),
            holdout=len(buckets.get("holdout", [])),
            edge=len(buckets.get("edge", [])),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
