#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT_DIR = Path(__file__).resolve().parents[1]
UNIFIED_PIPELINE = ROOT_DIR / "scripts/render-coconala-reply.py"
MODE_FILE = ROOT_DIR / "runtime/mode.txt"
SHADOW_DIR = ROOT_DIR / "runtime/rehearsal/coconala-reply-shadow"
RUNS_JSONL = SHADOW_DIR / "runs.jsonl"
JST = ZoneInfo("Asia/Tokyo")

DEFAULT_ROUTE_BY_STATE = {
    "prequote": "message",
    "quote_sent": "message",
    "purchased": "talkroom",
    "delivered": "talkroom",
    "closed": "message",
}

DEFAULT_SERVICE_HINT_BY_STATE = {
    "prequote": "bugfix",
    "quote_sent": "bugfix",
    "purchased": "bugfix",
    "delivered": "bugfix",
    "closed": "after_close",
}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_runtime_mode() -> str:
    if not MODE_FILE.exists():
        return ""
    return MODE_FILE.read_text(encoding="utf-8").strip()


def read_source_text(file_path: str | None, text_value: str | None) -> str:
    if file_path:
        return Path(file_path).read_text(encoding="utf-8").strip()
    if text_value:
        return text_value.strip()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    return ""


def build_case_id(provided: str | None, now: datetime) -> str:
    if provided:
        return provided
    return f"shadow-{now.strftime('%Y%m%d-%H%M%S-%f')}"


def build_run_key(generated_at: str, case_id: str) -> str:
    return f"{generated_at}|{case_id}"


def build_shadow_source(args, source_text: str, now: datetime) -> dict:
    case_id = build_case_id(args.case_id, now)
    return {
        "case_id": case_id,
        "id": case_id,
        "route": args.route or DEFAULT_ROUTE_BY_STATE[args.state],
        "state": args.state,
        "user_type": args.user_type,
        "emotional_tone": args.emotional_tone,
        "service_hint": args.service_hint or DEFAULT_SERVICE_HINT_BY_STATE[args.state],
        "raw_message": source_text,
        "note": args.note or "",
    }


def build_report_text(
    *,
    now: datetime,
    runtime_mode: str,
    source: dict,
    result: dict,
    saved: bool,
) -> str:
    case = result.get("case") or {}
    scenario = case.get("scenario") or ""
    decision_plan = case.get("response_decision_plan") or {}
    lines = [
        f"generated_at: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}",
        f"runtime_mode: {runtime_mode or '(missing)'}",
        f"case_id: {source.get('case_id', '')}",
        f"state: {source.get('state', '')}",
        f"route: {source.get('route', '')}",
        f"lane: {result.get('lane') or 'unsupported'}",
        f"scenario: {scenario}",
        f"lint_status: {'OK' if not result.get('errors') else 'NG'}",
        f"saved_to_runtime: {'yes' if saved else 'no'}",
    ]
    primary_concern = decision_plan.get("primary_concern")
    if primary_concern:
        lines.append(f"primary_concern: {primary_concern}")
    buyer_questions = (result.get("case") or {}).get("buyer_questions") or []
    if buyer_questions:
        lines.append(f"buyer_questions: {', '.join(item.get('id', '') for item in buyer_questions if item.get('id'))}")
    lines.extend(
        [
            "",
            "[source]",
            source.get("raw_message", ""),
            "",
            "[reply]",
            result.get("sendable_reply", ""),
        ]
    )
    errors = result.get("errors") or []
    if errors:
        lines.extend(["", "[errors]"])
        lines.extend(f"- {error}" for error in errors)
    return "\n".join(lines).rstrip() + "\n"


def save_shadow_report(now: datetime, report_text: str, report_payload: dict, *, case_id: str) -> tuple[Path, Path, Path, Path]:
    SHADOW_DIR.mkdir(parents=True, exist_ok=True)
    safe_case_id = case_id.replace("/", "-").replace(" ", "-")
    stamp = now.strftime("%Y%m%d-%H%M%S-%f")
    latest_txt = SHADOW_DIR / "latest.txt"
    history_txt = SHADOW_DIR / f"{stamp}-{safe_case_id}.txt"
    latest_json = SHADOW_DIR / "latest.json"
    history_json = SHADOW_DIR / f"{stamp}-{safe_case_id}.json"
    latest_txt.write_text(report_text, encoding="utf-8")
    history_txt.write_text(report_text, encoding="utf-8")
    payload_text = json.dumps(report_payload, ensure_ascii=False, indent=2) + "\n"
    latest_json.write_text(payload_text, encoding="utf-8")
    history_json.write_text(payload_text, encoding="utf-8")
    return latest_txt, history_txt, latest_json, history_json


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one shadow coconala reply through the unified pipeline.")
    parser.add_argument("--state", required=True, choices=["prequote", "quote_sent", "purchased", "delivered", "closed"])
    parser.add_argument("--source-file")
    parser.add_argument("--source-text")
    parser.add_argument("--route", choices=["message", "talkroom", "service", "profile"])
    parser.add_argument("--service-hint")
    parser.add_argument("--user-type", default="non_engineer")
    parser.add_argument("--emotional-tone", default="normal")
    parser.add_argument("--note")
    parser.add_argument("--case-id")
    parser.add_argument("--save", action="store_true", help="Save the sendable reply to runtime/replies/latest*.txt when lint passes.")
    parser.add_argument("--no-lint", action="store_true", help="Skip lane/common validator checks.")
    parser.add_argument("--allow-mode-mismatch", action="store_true")
    args = parser.parse_args()

    source_text = read_source_text(args.source_file, args.source_text)
    if not source_text:
        print("[NG] source text is required via --source-file, --source-text, or stdin")
        return 1

    runtime_mode = read_runtime_mode()
    if runtime_mode != "coconala" and not args.allow_mode_mismatch:
        print(f"[NG] runtime mode must be `coconala` for shadow reply runs: current={runtime_mode or '(missing)'}")
        return 1

    now = datetime.now(JST)
    source = build_shadow_source(args, source_text, now)
    unified = load_module("render_coconala_reply", UNIFIED_PIPELINE)
    tools = unified.load_tools()
    result = unified.run_pipeline(source, tools=tools, lint=not args.no_lint)

    saved = False
    if args.save:
        if result.get("errors"):
            print("[NG] reply was not saved because lint failed")
        else:
            tools["prequote"]["drafter"].save_reply(result["sendable_reply"], source_text)
            saved = True

    report_payload = {
        "generated_at": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "runtime_mode": runtime_mode,
        "source": source,
        "lane": result.get("lane"),
        "scenario": (result.get("case") or {}).get("scenario"),
        "buyer_questions": (result.get("case") or {}).get("buyer_questions") or [],
        "primary_concern": ((result.get("case") or {}).get("response_decision_plan") or {}).get("primary_concern"),
        "errors": result.get("errors") or [],
        "sendable_reply": result.get("sendable_reply") or "",
        "saved_to_runtime": saved,
    }
    report_payload["run_key"] = build_run_key(report_payload["generated_at"], source["case_id"])
    report_text = build_report_text(
        now=now,
        runtime_mode=runtime_mode,
        source=source,
        result=result,
        saved=saved,
    )
    latest_txt, history_txt, latest_json, history_json = save_shadow_report(
        now,
        report_text,
        report_payload,
        case_id=source["case_id"],
    )
    append_jsonl(RUNS_JSONL, report_payload)

    print(report_text.rstrip())
    print()
    print(f"shadow_latest_txt: {latest_txt}")
    print(f"shadow_history_txt: {history_txt}")
    print(f"shadow_latest_json: {latest_json}")
    print(f"shadow_history_json: {history_json}")
    print(f"shadow_runs_jsonl: {RUNS_JSONL}")

    if result.get("errors"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
