#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT_DIR = Path(__file__).resolve().parents[1]
SHADOW_DIR = ROOT_DIR / "runtime/rehearsal/coconala-reply-shadow"
ARCHIVE_DIR = SHADOW_DIR / "archive"
JST = ZoneInfo("Asia/Tokyo")

ARCHIVE_PATTERNS = [
    "20*.json",
    "20*.txt",
    "latest.json",
    "latest.txt",
    "latest-review.json",
    "latest-review.txt",
    "summary-latest.json",
    "summary-latest.txt",
    "status-latest.json",
    "status-latest.txt",
    "runs.jsonl",
    "reviews.jsonl",
    "exported-reviews.jsonl",
    "smoke-export.txt",
]


def collect_targets() -> list[Path]:
    seen: set[Path] = set()
    targets: list[Path] = []
    for pattern in ARCHIVE_PATTERNS:
        for path in sorted(SHADOW_DIR.glob(pattern)):
            if path.is_file() and path not in seen:
                seen.add(path)
                targets.append(path)
    return targets


def build_archive_path(name: str | None) -> Path:
    stamp = datetime.now(JST).strftime("%Y%m%d-%H%M%S")
    suffix = name.strip() if name else "shadow-session"
    safe_suffix = suffix.replace("/", "-").replace(" ", "-")
    return ARCHIVE_DIR / f"{stamp}-{safe_suffix}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive current coconala shadow session artifacts and reset active ledgers.")
    parser.add_argument("--name", help="Optional archive label suffix, for example smoke-baseline")
    args = parser.parse_args()

    if not SHADOW_DIR.exists():
        print("[OK] no shadow directory found")
        return 0

    targets = collect_targets()
    if not targets:
        print("[OK] no active shadow artifacts to archive")
        return 0

    archive_path = build_archive_path(args.name)
    archive_path.mkdir(parents=True, exist_ok=True)

    moved: list[Path] = []
    for path in targets:
        destination = archive_path / path.name
        path.rename(destination)
        moved.append(destination)

    print(f"archive: {archive_path}")
    print(f"moved: {len(moved)}")
    for path in moved:
        print(f"- {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
