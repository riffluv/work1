#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT_DIR = Path(__file__).resolve().parents[1]
FULL_REGRESSION = ROOT_DIR / "scripts/check-coconala-reply-full-regression.py"
REPORT_DIR = ROOT_DIR / "runtime/regression/coconala-reply/suites"
JST = ZoneInfo("Asia/Tokyo")
DEFAULT_ROLES = ["seed", "renderer_seed", "edge", "eval", "holdout"]


def run_role(role: str) -> tuple[int, str]:
    proc = subprocess.run(
        ["python3", str(FULL_REGRESSION), "--role", role],
        capture_output=True,
        text=True,
    )
    output = ((proc.stdout or "") + (proc.stderr or "")).strip()
    return proc.returncode, output


def build_report_text(started_at: datetime, results: list[tuple[str, int, str]]) -> str:
    lines = [f"generated_at: {started_at.strftime('%Y-%m-%d %H:%M:%S %Z')}", "", "[roles]"]
    overall_ok = True
    for role, status, output in results:
        if status != 0:
            overall_ok = False
        lines.append(f"{role}: {'OK' if status == 0 else 'NG'}")
        lines.append("")
        lines.append(f"[{role}]")
        lines.append(output or "<no output>")
        lines.append("")
    lines.append("[status]")
    lines.append("[OK] coconala reply role suites passed" if overall_ok else "[NG] coconala reply role suites failed")
    return "\n".join(lines).rstrip() + "\n"


def save_report(text: str, started_at: datetime) -> tuple[Path, Path]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = started_at.strftime("%Y%m%d-%H%M%S")
    latest_path = REPORT_DIR / "latest.txt"
    history_path = REPORT_DIR / f"{stamp}.txt"
    latest_path.write_text(text, encoding="utf-8")
    history_path.write_text(text, encoding="utf-8")
    return latest_path, history_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run full regression per role suite.")
    parser.add_argument("--role", action="append", help="Role to run. Repeatable.")
    parser.add_argument("--save-report", action="store_true")
    args = parser.parse_args()

    started_at = datetime.now(JST)
    roles = args.role or DEFAULT_ROLES
    results: list[tuple[str, int, str]] = []
    for role in roles:
        status, output = run_role(role)
        results.append((role, status, output))

    report_text = build_report_text(started_at, results)
    if args.save_report:
        latest_path, history_path = save_report(report_text, started_at)
        print(f"report_latest: {latest_path}")
        print(f"report_history: {history_path}")
    print(report_text.rstrip())
    return 0 if all(status == 0 for _, status, _ in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
