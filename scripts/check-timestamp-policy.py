#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT_DIR = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT_DIR / "runtime/regression/timestamp-policy"
JST = ZoneInfo("Asia/Tokyo")
TIME_COMMIT_RE = re.compile(r"本日(?P<hour>\d{1,2}):(?P<minute>\d{2})までに")
RUNTIME_FIXTURES = [
    ROOT_DIR / "ops/tests/quality-cases/active/delivery-completion-bugfix40.yaml",
    ROOT_DIR / "ops/tests/quality-cases/active/live-core-human-review-bugfix43.yaml",
    ROOT_DIR / "ops/tests/quality-cases/active/public-launch-practical-bugfix44.yaml",
    ROOT_DIR / "ops/tests/quality-cases/active/post-pro-grounding-bugfix45.yaml",
    ROOT_DIR / "ops/tests/quality-cases/active/post-pro-review-lenses-bugfix46.yaml",
    ROOT_DIR / "ops/tests/quality-cases/active/post-pro-native-naturalness-bugfix47.yaml",
    ROOT_DIR / "ops/tests/quality-cases/active/live-practical-naturalness-bugfix48.yaml",
]
CURRENT_REHEARSAL_FILES = [
    ROOT_DIR / "サービスページ/rehearsal/bugfix-15000-返信学習/返信監査_batch-01.md",
    ROOT_DIR / "サービスページ/rehearsal/boundary-routing-返信学習/返信監査_batch-current.md",
]
RENDERER_FILES = [
    ROOT_DIR / "scripts/render-post-purchase-quick.py",
    ROOT_DIR / "scripts/render-delivered-followup.py",
    ROOT_DIR / "scripts/render-closed-followup.py",
]


def minutes_until_today_deadline(now: datetime, hour: int, minute: int) -> int:
    deadline = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return int((deadline - now).total_seconds() // 60)


def run_renderer(fixture: Path) -> tuple[int, str]:
    proc = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/render-coconala-reply.py"), "--fixture", str(fixture), "--lint"],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
    )
    return proc.returncode, ((proc.stdout or "") + (proc.stderr or "")).strip()


def extract_time_commits(text: str) -> list[tuple[int, int, str]]:
    commits: list[tuple[int, int, str]] = []
    for match in TIME_COMMIT_RE.finditer(text):
        hour = int(match.group("hour"))
        minute = int(match.group("minute"))
        commits.append((hour, minute, match.group(0)))
    return commits


def check_runtime_outputs(now: datetime) -> tuple[list[str], list[str], list[str]]:
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []
    for fixture in RUNTIME_FIXTURES:
        label = str(fixture.relative_to(ROOT_DIR))
        status, rendered = run_renderer(fixture)
        if status != 0:
            failures.append(f"[NG] runtime_timestamp:{label}: renderer/lint failed")
            failures.append(rendered)
            continue
        commits = extract_time_commits(rendered)
        if not commits:
            passes.append(f"[OK] runtime_timestamp:{label}: no concrete time commitments")
            continue
        for hour, minute, text in commits:
            if hour > 23 or minute > 59:
                failures.append(f"[NG] runtime_timestamp:{label}: invalid time {text}")
                continue
            delta = minutes_until_today_deadline(now, hour, minute)
            if delta <= 0:
                failures.append(f"[NG] runtime_timestamp:{label}: stale or past commitment {text}")
            elif delta > 8 * 60:
                warnings.append(f"[WARN] runtime_timestamp:{label}: far future same-day commitment {text} ({delta} min)")
            else:
                passes.append(f"[OK] runtime_timestamp:{label}: runtime commitment {text} ({delta} min)")
    return passes, warnings, failures


def check_renderer_sources() -> tuple[list[str], list[str]]:
    passes: list[str] = []
    failures: list[str] = []
    for path in RENDERER_FILES:
        label = str(path.relative_to(ROOT_DIR))
        text = path.read_text(encoding="utf-8")
        hardcoded = re.findall(r"本日\d{1,2}:\d{2}までに", text)
        if hardcoded:
            failures.append(f"[NG] renderer_timestamp_source:{label}: hard-coded timestamp literal(s): {', '.join(sorted(set(hardcoded)))}")
            continue
        if "datetime.now(JST)" in text and "timedelta" in text:
            passes.append(f"[OK] renderer_timestamp_source:{label}: uses runtime datetime source")
        else:
            passes.append(f"[OK] renderer_timestamp_source:{label}: no runtime timestamp source required")
    return passes, failures


def check_static_rehearsal_files() -> tuple[list[str], list[str]]:
    passes: list[str] = []
    warnings: list[str] = []
    for path in CURRENT_REHEARSAL_FILES:
        label = str(path.relative_to(ROOT_DIR))
        if not path.exists():
            warnings.append(f"[WARN] static_timestamp:{label}: file missing")
            continue
        text = path.read_text(encoding="utf-8")
        commits = extract_time_commits(text)
        if not commits:
            passes.append(f"[OK] static_timestamp:{label}: no fixed concrete timestamps")
            continue
        samples = ", ".join(commit for _, _, commit in commits[:5])
        warnings.append(
            f"[WARN] static_timestamp:{label}: fixed timestamp sample(s) remain: {samples}; "
            "regenerate before external review if freshness matters"
        )
    return passes, warnings


def build_report_text(
    started_at: datetime,
    passes: list[str],
    warnings: list[str],
    failures: list[str],
) -> str:
    lines = [
        f"generated_at: {started_at.strftime('%Y-%m-%d %H:%M:%S %Z')}",
        f"pass: {len(passes)}",
        f"warn: {len(warnings)}",
        f"fail: {len(failures)}",
        "",
        "[passes]",
    ]
    lines.extend(passes or ["<none>"])
    if warnings:
        lines.extend(["", "[warnings]"])
        lines.extend(warnings)
    if failures:
        lines.extend(["", "[failures]"])
        lines.extend(failures)
    lines.extend(["", "[status]"])
    if failures:
        lines.append("[NG] timestamp policy failed")
    elif warnings:
        lines.append("[OK] timestamp policy passed with warnings")
    else:
        lines.append("[OK] timestamp policy passed")
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
    parser = argparse.ArgumentParser(description="Check timestamp commitments in rendered replies and active rehearsal docs.")
    parser.add_argument("--save-report", action="store_true")
    parser.add_argument("--fail-on-warnings", action="store_true")
    args = parser.parse_args()

    started_at = datetime.now(JST)
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    runtime_passes, runtime_warnings, runtime_failures = check_runtime_outputs(started_at)
    renderer_passes, renderer_failures = check_renderer_sources()
    static_passes, static_warnings = check_static_rehearsal_files()
    passes.extend(runtime_passes)
    passes.extend(renderer_passes)
    passes.extend(static_passes)
    warnings.extend(runtime_warnings)
    warnings.extend(static_warnings)
    failures.extend(runtime_failures)
    failures.extend(renderer_failures)
    if args.fail_on_warnings and warnings:
        failures.extend(f"[WARN->NG] {warning[7:] if warning.startswith('[WARN] ') else warning}" for warning in warnings)

    report_text = build_report_text(started_at, passes, warnings, failures)
    if args.save_report:
        latest_path, history_path = save_report(report_text, started_at)
        print(f"report_latest: {latest_path}")
        print(f"report_history: {history_path}")
    print(report_text.rstrip())
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
