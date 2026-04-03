#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
import re
from zoneinfo import ZoneInfo

import yaml


ROOT_DIR = Path(__file__).resolve().parents[1]
EVAL_SOURCES = ROOT_DIR / "ops/tests/eval-sources.yaml"
UNIFIED_RENDERER = ROOT_DIR / "scripts/render-coconala-reply.py"
REGRESSION_DIR = ROOT_DIR / "runtime/regression/coconala-reply"
FAILURE_DIR = REGRESSION_DIR / "failures"
JST = ZoneInfo("Asia/Tokyo")
SUMMARY_RE = re.compile(
    r"^(?P<name>[^:]+): pass=(?P<pass>\d+) fail=(?P<fail>\d+) skip=(?P<skip>\d+) "
    r"\(prequote=(?P<pass_prequote>\d+)/(?P<fail_prequote>\d+) "
    r"quote_sent=(?P<pass_quote_sent>\d+)/(?P<fail_quote_sent>\d+) "
    r"purchased=(?P<pass_purchased>\d+)/(?P<fail_purchased>\d+) "
    r"closed=(?P<pass_closed>\d+)/(?P<fail_closed>\d+) "
    r"(?:delivered=(?P<pass_delivered>\d+)/(?P<fail_delivered>\d+))?\)$"
)
TOTAL_RE = re.compile(r"^TOTAL: pass=(?P<pass>\d+) fail=(?P<fail>\d+) skip=(?P<skip>\d+)$")
SKIP_REASON_RE = re.compile(
    r"^(?P<name>[^:]+): unimplemented=(?P<unimplemented>\d+) "
    r"out_of_scope=(?P<out_of_scope>\d+) skeleton=(?P<skeleton>\d+)$"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_active_sources(
    config_path: Path,
    include_secondary: bool,
    roles: set[str] | None = None,
    exclude_roles: set[str] | None = None,
) -> list[dict]:
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    sources = [item for item in data.get("primary_sources", []) if item.get("status") == "active"]
    if include_secondary:
        sources.extend(item for item in data.get("secondary_sources", []) if item.get("status") == "active")
    filtered: list[dict] = []
    for item in sources:
        role = item.get("role")
        if roles and role not in roles:
            continue
        if exclude_roles and role in exclude_roles:
            continue
        filtered.append(item)
    return filtered


def state_bucket(case: dict) -> str:
    state = case.get("state") or "unknown"
    if state in {"prequote", "quote_sent", "purchased", "closed", "delivered"}:
        return state
    return "unsupported"


def build_summary_lines(source_name: str, counter: Counter) -> str:
    return (
        f"{source_name}: pass={counter['pass']} fail={counter['fail']} skip={counter['skip']} "
        f"(prequote={counter['pass_prequote']}/{counter['fail_prequote']} "
        f"quote_sent={counter['pass_quote_sent']}/{counter['fail_quote_sent']} "
        f"purchased={counter['pass_purchased']}/{counter['fail_purchased']} "
        f"closed={counter['pass_closed']}/{counter['fail_closed']} "
        f"delivered={counter['pass_delivered']}/{counter['fail_delivered']})"
    )


def build_skip_reason_line(source_name: str, counter: Counter) -> str:
    return (
        f"{source_name}: unimplemented={counter['skip_unimplemented_state']} "
        f"out_of_scope={counter['skip_out_of_scope_state']} "
        f"skeleton={counter['skip_unsupported_skeleton']}"
    )


def classify_skip_reason(case: dict, lane: str | None) -> str:
    state = case.get("state") or "unknown"
    if lane is None and (case.get("reply_stance") or {}).get("reply_skeleton"):
        return "skip_unsupported_skeleton"
    if state in {"predelivery"}:
        return "skip_unimplemented_state"
    return "skip_out_of_scope_state"


def build_report_text(
    started_at: datetime,
    sources: list[dict],
    source_counters: dict[str, Counter],
    totals: Counter,
    failures: list[str],
    failure_details: list[str],
    skip_details: list[str],
    passes: list[str],
    show_passes: bool,
) -> str:
    lines = [
        f"generated_at: {started_at.strftime('%Y-%m-%d %H:%M:%S %Z')}",
        f"total_pass: {totals['pass']}",
        f"total_fail: {totals['fail']}",
        f"total_skip: {totals['skip']}",
        "",
        "[sources]",
    ]

    for source in sources:
        path = Path(source["path"])
        lines.append(build_summary_lines(path.name, source_counters[path.name]))

    lines.extend(["", "[skip_reasons]"])
    for source in sources:
        path = Path(source["path"])
        lines.append(build_skip_reason_line(path.name, source_counters[path.name]))

    lines.extend(["", f"TOTAL: pass={totals['pass']} fail={totals['fail']} skip={totals['skip']}"])

    if skip_details:
        lines.extend(["", "[skips]"])
        lines.extend(skip_details)

    if show_passes and passes:
        lines.extend(["", "[passes]"])
        lines.extend(passes)

    if failures:
        lines.extend(["", "[failures]"])
        lines.extend(failures)
        if failure_details:
            lines.extend(["", "[failure_details]"])
            lines.extend(failure_details)
    else:
        lines.extend(["", "[status]", "[OK] coconala reply regression passed"])

    return "\n".join(lines) + "\n"


def save_report(report_text: str, started_at: datetime) -> tuple[Path, Path]:
    REGRESSION_DIR.mkdir(parents=True, exist_ok=True)
    stamp = started_at.strftime("%Y%m%d-%H%M%S")
    latest_path = REGRESSION_DIR / "latest.txt"
    history_path = REGRESSION_DIR / f"{stamp}.txt"
    latest_path.write_text(report_text, encoding="utf-8")
    history_path.write_text(report_text, encoding="utf-8")
    return latest_path, history_path


def build_failure_detail_block(
    key: str,
    lane: str,
    state: str,
    errors: list[str],
    raw_message: str,
    rendered_reply: str | None,
) -> str:
    lines = [
        f"- case: {key}",
        f"  lane: {lane}",
        f"  state: {state}",
        "  errors:",
    ]
    for error in errors:
        lines.append(f"    - {error}")
    lines.extend(
        [
            "  raw_message: |",
            *(f"    {line}" for line in (raw_message.splitlines() or [""])),
        ]
    )
    if rendered_reply is not None:
        lines.extend(
            [
                "  rendered_reply: |",
                *(f"    {line}" for line in (rendered_reply.splitlines() or [""])),
            ]
        )
    return "\n".join(lines)


def build_failure_details_text(started_at: datetime, failure_details: list[str]) -> str:
    lines = [f"generated_at: {started_at.strftime('%Y-%m-%d %H:%M:%S %Z')}"]
    if failure_details:
        lines.extend(["", "[failure_details]"])
        lines.extend(failure_details)
    else:
        lines.extend(["", "[status]", "[OK] no failure details"])
    return "\n".join(lines) + "\n"


def save_failure_details(details_text: str, started_at: datetime) -> tuple[Path, Path]:
    FAILURE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = started_at.strftime("%Y%m%d-%H%M%S")
    latest_path = FAILURE_DIR / "latest.txt"
    history_path = FAILURE_DIR / f"{stamp}.txt"
    latest_path.write_text(details_text, encoding="utf-8")
    history_path.write_text(details_text, encoding="utf-8")
    return latest_path, history_path


def parse_report_text(report_text: str) -> tuple[dict[str, Counter], Counter]:
    source_counters: dict[str, Counter] = {}
    totals = Counter()

    for raw_line in report_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        summary_match = SUMMARY_RE.match(line)
        if summary_match:
            counter = Counter()
            for key, value in summary_match.groupdict().items():
                if key == "name":
                    continue
                counter[key] = int(value) if value is not None else 0
            source_counters[summary_match.group("name")] = counter
            continue

        skip_reason_match = SKIP_REASON_RE.match(line)
        if skip_reason_match:
            counter = source_counters.get(skip_reason_match.group("name"), Counter())
            counter["skip_unimplemented_state"] = int(skip_reason_match.group("unimplemented"))
            counter["skip_out_of_scope_state"] = int(skip_reason_match.group("out_of_scope"))
            counter["skip_unsupported_skeleton"] = int(skip_reason_match.group("skeleton"))
            source_counters[skip_reason_match.group("name")] = counter
            continue

        total_match = TOTAL_RE.match(line)
        if total_match:
            for key, value in total_match.groupdict().items():
                totals[key] = int(value)

    return source_counters, totals


def delta_str(current: int, previous: int) -> str:
    diff = current - previous
    if diff > 0:
        return f"+{diff}"
    return str(diff)


def build_diff_text(
    previous_text: str,
    current_text: str,
    started_at: datetime,
) -> str:
    prev_sources, prev_totals = parse_report_text(previous_text)
    curr_sources, curr_totals = parse_report_text(current_text)

    source_names = sorted(set(prev_sources) | set(curr_sources))
    lines = [
        f"generated_at: {started_at.strftime('%Y-%m-%d %H:%M:%S %Z')}",
        "[totals]",
        (
            f"pass: {curr_totals['pass']} ({delta_str(curr_totals['pass'], prev_totals['pass'])}) "
            f"fail: {curr_totals['fail']} ({delta_str(curr_totals['fail'], prev_totals['fail'])}) "
            f"skip: {curr_totals['skip']} ({delta_str(curr_totals['skip'], prev_totals['skip'])})"
        ),
        "",
        "[sources]",
    ]

    for name in source_names:
        prev = prev_sources.get(name, Counter())
        curr = curr_sources.get(name, Counter())
        lines.append(
            f"{name}: "
            f"pass={curr['pass']} ({delta_str(curr['pass'], prev['pass'])}) "
            f"fail={curr['fail']} ({delta_str(curr['fail'], prev['fail'])}) "
            f"skip={curr['skip']} ({delta_str(curr['skip'], prev['skip'])}) "
            f"prequote={curr['pass_prequote']}/{curr['fail_prequote']} "
            f"quote_sent={curr['pass_quote_sent']}/{curr['fail_quote_sent']} "
            f"purchased={curr['pass_purchased']}/{curr['fail_purchased']} "
            f"closed={curr['pass_closed']}/{curr['fail_closed']} "
            f"delivered={curr['pass_delivered']}/{curr['fail_delivered']}"
        )

    lines.extend(["", "[skip_reasons]"])
    for name in source_names:
        prev = prev_sources.get(name, Counter())
        curr = curr_sources.get(name, Counter())
        lines.append(
            f"{name}: "
            f"unimplemented={curr['skip_unimplemented_state']} ({delta_str(curr['skip_unimplemented_state'], prev['skip_unimplemented_state'])}) "
            f"out_of_scope={curr['skip_out_of_scope_state']} ({delta_str(curr['skip_out_of_scope_state'], prev['skip_out_of_scope_state'])}) "
            f"skeleton={curr['skip_unsupported_skeleton']} ({delta_str(curr['skip_unsupported_skeleton'], prev['skip_unsupported_skeleton'])})"
        )

    return "\n".join(lines) + "\n"


def save_diff(diff_text: str, started_at: datetime) -> tuple[Path, Path]:
    stamp = started_at.strftime("%Y%m%d-%H%M%S")
    latest_path = REGRESSION_DIR / "latest-diff.txt"
    history_path = REGRESSION_DIR / f"{stamp}.diff.txt"
    latest_path.write_text(diff_text, encoding="utf-8")
    history_path.write_text(diff_text, encoding="utf-8")
    return latest_path, history_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch regression runner for coconala reply renderers.")
    parser.add_argument("--config", default=str(EVAL_SOURCES))
    parser.add_argument("--source")
    parser.add_argument("--include-secondary", action="store_true")
    parser.add_argument("--role", action="append", help="Only include sources with this role. Repeatable.")
    parser.add_argument("--exclude-role", action="append", help="Exclude sources with this role. Repeatable.")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--show-passes", action="store_true")
    parser.add_argument("--save-report", action="store_true")
    parser.add_argument("--show-diff", action="store_true")
    args = parser.parse_args()

    started_at = datetime.now(JST)
    unified = load_module("render_coconala_reply", UNIFIED_RENDERER)
    tools = unified.load_tools()
    estimate_renderer = tools["prequote"]["renderer"]
    roles = set(args.role or [])
    exclude_roles = set(args.exclude_role or [])
    sources = load_active_sources(Path(args.config), args.include_secondary, roles=roles or None, exclude_roles=exclude_roles or None)

    if args.source:
        sources = [item for item in sources if item.get("path") == args.source]
    if not sources:
        print("[NG] no active evaluation sources selected")
        return 1

    totals = Counter()
    source_counters: dict[str, Counter] = defaultdict(Counter)
    failures: list[str] = []
    failure_details: list[str] = []
    skip_details: list[str] = []
    passes: list[str] = []

    for source in sources:
        path = Path(source["path"])
        cases = estimate_renderer.load_cases(path)
        if args.limit is not None:
            cases = cases[: args.limit]

        for case in cases:
            case_id = case.get("case_id") or case.get("id") or "<unknown>"
            state = state_bucket(case)
            key = f"{path.name}:{case_id}"

            if state == "unsupported":
                totals["skip"] += 1
                source_counters[path.name]["skip"] += 1
                reason = classify_skip_reason(case, None)
                source_counters[path.name][reason] += 1
                skip_details.append(f"[SKIP] {key}: {reason}")
                continue

            lane = unified.choose_lane(case)
            if lane is None:
                totals["skip"] += 1
                source_counters[path.name]["skip"] += 1
                reason = classify_skip_reason(case, None)
                source_counters[path.name][reason] += 1
                skip_details.append(f"[SKIP] {key}: {reason}")
                continue

            tool = tools[lane]
            reply = tool["render_fn"](tool["renderer"], case)
            errors = tool["lint_fn"](case)
            if errors:
                totals["fail"] += 1
                source_counters[path.name]["fail"] += 1
                source_counters[path.name][f"fail_{lane}"] += 1
                for error in errors:
                    failures.append(f"[NG] {key}: {error}")
                failure_details.append(
                    build_failure_detail_block(
                        key=key,
                        lane=lane,
                        state=case.get("state", "unknown"),
                        errors=errors,
                        raw_message=case.get("raw_message", ""),
                        rendered_reply=reply,
                    )
                )
                continue

            totals["pass"] += 1
            source_counters[path.name]["pass"] += 1
            source_counters[path.name][f"pass_{lane}"] += 1
            passes.append(f"[OK] {key}: {lane}")

    summary_lines: list[str] = []
    for source in sources:
        path = Path(source["path"])
        line = build_summary_lines(path.name, source_counters[path.name])
        summary_lines.append(line)
        print(line)
        skip_line = build_skip_reason_line(path.name, source_counters[path.name])
        print(f"  skip_reasons: {skip_line.split(': ', 1)[1]}")

    print(f"TOTAL: pass={totals['pass']} fail={totals['fail']} skip={totals['skip']}")

    report_text = build_report_text(
        started_at=started_at,
        sources=sources,
        source_counters=source_counters,
        totals=totals,
        failures=failures,
        failure_details=failure_details,
        skip_details=skip_details,
        passes=passes,
        show_passes=args.show_passes,
    )
    previous_report_text = None
    previous_latest_path = REGRESSION_DIR / "latest.txt"
    if args.save_report and previous_latest_path.exists():
        previous_report_text = previous_latest_path.read_text(encoding="utf-8")

    if args.save_report:
        latest_path, history_path = save_report(report_text, started_at)
        print(f"report_latest: {latest_path}")
        print(f"report_history: {history_path}")
        failure_text = build_failure_details_text(started_at, failure_details)
        failure_latest_path, failure_history_path = save_failure_details(failure_text, started_at)
        print(f"failure_latest: {failure_latest_path}")
        print(f"failure_history: {failure_history_path}")
        if previous_report_text is not None:
            diff_text = build_diff_text(previous_report_text, report_text, started_at)
            diff_latest_path, diff_history_path = save_diff(diff_text, started_at)
            print(f"diff_latest: {diff_latest_path}")
            print(f"diff_history: {diff_history_path}")
            if args.show_diff:
                print()
                print(diff_text.rstrip())

    if args.show_passes and passes:
        print()
        for line in passes:
            print(line)

    if skip_details:
        print()
        for line in skip_details:
            print(line)

    if failures:
        print()
        for line in failures:
            print(line)
        return 1

    print()
    print("[OK] coconala reply regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
