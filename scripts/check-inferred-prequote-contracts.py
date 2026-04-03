#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml


ROOT_DIR = Path(__file__).resolve().parents[1]
RENDERER_PATH = ROOT_DIR / "scripts/render-prequote-estimate-initial.py"
DEFAULT_FIXTURES = [
    ROOT_DIR / "ops/tests/prequote-bulk-20-v6.txt",
    ROOT_DIR / "ops/tests/prequote-test-cases.txt",
]
DEFAULT_CONFIG = ROOT_DIR / "ops/tests/eval-sources.yaml"
REPORT_DIR = ROOT_DIR / "runtime/regression/coconala-reply/contracts"
JST = ZoneInfo("Asia/Tokyo")

CASE_EXPECTATIONS = {
    "V6-001": {
        "primary_contains": "15,000円で対応できるか",
        "primary_disposition": "answer_after_check",
        "min_questions": 4,
        "ask_count": 1,
        "question_dispositions": {
            "Stripeの問題": "answer_after_check",
            "税込み": "answer_now",
            "今週中": "answer_after_check",
        },
    },
    "V6-003": {
        "primary_contains": "見てもら",
        "primary_disposition": "answer_after_check",
        "ask_count": 1,
        "question_dispositions": {
            "不正アクセス": "answer_after_check",
        },
    },
    "V6-005": {
        "primary_contains": "見てもら",
        "primary_disposition": "answer_now",
        "ask_count": 0,
        "question_dispositions": {
            ".env": "answer_now",
            "スクショ": "answer_now",
        },
    },
    "V6-008": {
        "primary_contains": "見てもら",
        "primary_disposition": "answer_after_check",
        "ask_count": 1,
        "question_dispositions": {
            "直接会って": "answer_now",
        },
    },
    "V6-009": {
        "primary_contains": "見てもら",
        "primary_disposition": "answer_after_check",
        "ask_count": 1,
        "question_dispositions": {
            "内容にどんな差": "answer_after_check",
        },
    },
    "V6-010": {
        "primary_contains": "見てもら",
        "primary_disposition": "answer_after_check",
        "ask_count": 1,
        "question_dispositions": {
            "これって不具合": "answer_after_check",
            "直してもらえますか": "answer_after_check",
        },
    },
    "V6-011": {
        "primary_contains": "見てもら",
        "primary_disposition": "answer_after_check",
        "ask_count": 1,
        "question_dispositions": {
            "25,000円の方が安全": "answer_after_check",
            "修正含まない": "answer_after_check",
        },
    },
    "V6-013": {
        "primary_contains": "見てもら",
        "primary_disposition": "answer_now",
        "ask_count": 0,
        "question_dispositions": {
            "もっと安く": "answer_now",
        },
    },
    "V6-014": {
        "primary_contains": "表示速度が遅い",
        "primary_disposition": "answer_after_check",
        "ask_count": 1,
    },
    "MSG-002": {
        "primary_contains": "見てもら",
        "primary_disposition": "answer_after_check",
        "ask_count": 1,
        "question_dispositions": {
            "放置するとまずい": "answer_after_check",
            "相談だけでも": "answer_now",
        },
    },
    "MUL-003": {
        "primary_contains": "見てもら",
        "primary_disposition": "answer_after_check",
        "min_questions": 4,
        "ask_count": 1,
        "question_dispositions": {
            "完了ページ": "answer_after_check",
            "メールが飛ばない": "answer_after_check",
            "管理画面にデータ": "answer_after_check",
        },
    },
}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_fixtures_from_config(
    config_path: Path,
    roles: set[str] | None = None,
    exclude_roles: set[str] | None = None,
) -> list[Path]:
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    fixtures: list[Path] = []
    for item in data.get("primary_sources", []):
        if item.get("status") != "active":
            continue
        role = item.get("role")
        if roles and role not in roles:
            continue
        if exclude_roles and role in exclude_roles:
            continue
        fixtures.append(Path(item["path"]))
    return fixtures


def normalize_case(renderer, case: dict) -> dict:
    return case if case.get("reply_contract") else renderer.build_case_from_source(case)


def primary_question_text(contract: dict) -> str:
    primary_id = contract["primary_question_id"]
    for item in contract.get("explicit_questions") or []:
        if item.get("id") == primary_id:
            return item.get("text", "")
    return ""


def answer_map_by_question(contract: dict) -> dict[str, dict]:
    return {item["question_id"]: item for item in contract.get("answer_map") or []}


def find_question_id(contract: dict, text_fragment: str) -> str | None:
    for item in contract.get("explicit_questions") or []:
        if text_fragment in item.get("text", ""):
            return item.get("id")
    return None


def generic_checks(case: dict, built: dict) -> list[str]:
    errors: list[str] = []
    contract = built.get("reply_contract") or {}
    questions = contract.get("explicit_questions") or []
    answers = contract.get("answer_map") or []
    ask_map = contract.get("ask_map") or []
    question_ids = [item.get("id") for item in questions]
    primary_id = contract.get("primary_question_id")
    answers_by_id = answer_map_by_question(contract)

    if not questions:
        errors.append("explicit_questions missing")
    if primary_id not in question_ids:
        errors.append("primary_question_id is not in explicit_questions")

    if len(set(question_ids)) != len(question_ids):
        errors.append("duplicate explicit question ids")

    if set(question_ids) != set(answers_by_id):
        missing = sorted(set(question_ids) - set(answers_by_id))
        extra = sorted(set(answers_by_id) - set(question_ids))
        if missing:
            errors.append(f"answer_map missing question ids: {', '.join(missing)}")
        if extra:
            errors.append(f"answer_map has unknown question ids: {', '.join(extra)}")

    primary_answer = answers_by_id.get(primary_id)
    if primary_answer is None:
        errors.append("primary answer missing from answer_map")
    else:
        expected_timing = "after_check" if primary_answer.get("disposition") == "answer_after_check" else "now"
        actual_timing = ((built.get("reply_stance") or {}).get("answer_timing")) or ""
        if actual_timing != expected_timing:
            errors.append(
                f"reply_stance.answer_timing mismatch: expected {expected_timing}, got {actual_timing or '<missing>'}"
            )
        if primary_answer.get("disposition") == "answer_after_check":
            if not ask_map:
                errors.append("primary answer is answer_after_check but ask_map is empty")
            if not primary_answer.get("hold_reason"):
                errors.append("primary answer_after_check is missing hold_reason")
            if not primary_answer.get("revisit_trigger"):
                errors.append("primary answer_after_check is missing revisit_trigger")

    for answer in answers:
        if answer.get("disposition") == "answer_after_check":
            if not answer.get("hold_reason"):
                errors.append(f"{answer['question_id']} missing hold_reason")
            if not answer.get("revisit_trigger"):
                errors.append(f"{answer['question_id']} missing revisit_trigger")

    linked_question_ids: set[str] = set()
    for ask in ask_map:
        linked_ids = ask.get("question_ids") or []
        for question_id in linked_ids:
            linked_question_ids.add(question_id)
            if question_id not in question_ids:
                errors.append(f"ask_map references unknown question_id: {question_id}")
        if not ask.get("ask_text"):
            errors.append(f"{ask.get('id', '<unknown>')} missing ask_text")
        if not ask.get("why_needed"):
            errors.append(f"{ask.get('id', '<unknown>')} missing why_needed")

    ask_count = built.get("ask_count")
    if ask_count != len(ask_map):
        errors.append(f"ask_count mismatch: expected {len(ask_map)}, got {ask_count}")

    if primary_answer and primary_answer.get("disposition") == "answer_now" and ask_map:
        errors.append("primary answer_now should not emit ask_map")

    for question_id in linked_question_ids:
        answer = answers_by_id.get(question_id)
        if answer is None:
            continue
        if answer.get("disposition") == "answer_now":
            errors.append(f"ask_map points to answer_now question: {question_id}")

    return errors


def expectation_checks(case_id: str, built: dict) -> list[str]:
    expected = CASE_EXPECTATIONS.get(case_id)
    if not expected:
        return []

    errors: list[str] = []
    contract = built["reply_contract"]
    primary_id = contract["primary_question_id"]
    primary_text = primary_question_text(contract)
    answers_by_id = answer_map_by_question(contract)
    primary_answer = answers_by_id.get(primary_id, {})

    if expected.get("primary_contains") and expected["primary_contains"] not in primary_text:
        errors.append(
            f"primary question mismatch: expected fragment '{expected['primary_contains']}', got '{primary_text}'"
        )

    if expected.get("primary_disposition") and primary_answer.get("disposition") != expected["primary_disposition"]:
        errors.append(
            "primary disposition mismatch: "
            f"expected {expected['primary_disposition']}, got {primary_answer.get('disposition', '<missing>')}"
        )

    min_questions = expected.get("min_questions")
    if min_questions and len(contract.get("explicit_questions") or []) < min_questions:
        errors.append(
            f"explicit question count too small: expected at least {min_questions}, "
            f"got {len(contract.get('explicit_questions') or [])}"
        )

    expected_ask_count = expected.get("ask_count")
    if expected_ask_count is not None and len(contract.get("ask_map") or []) != expected_ask_count:
        errors.append(
            f"ask_map count mismatch: expected {expected_ask_count}, got {len(contract.get('ask_map') or [])}"
        )

    for fragment, disposition in (expected.get("question_dispositions") or {}).items():
        question_id = find_question_id(contract, fragment)
        if question_id is None:
            errors.append(f"expected question fragment not found: {fragment}")
            continue
        actual = answers_by_id.get(question_id, {}).get("disposition")
        if actual != disposition:
            errors.append(
                f"question disposition mismatch for '{fragment}': expected {disposition}, got {actual or '<missing>'}"
            )

    return errors


def build_report_text(started_at: datetime, counters: Counter, passes: list[str], failures: list[str]) -> str:
    lines = [
        f"generated_at: {started_at.strftime('%Y-%m-%d %H:%M:%S %Z')}",
        f"pass: {counters['pass']}",
        f"fail: {counters['fail']}",
        f"skip: {counters['skip']}",
    ]
    if passes:
        lines.extend(["", "[passes]"])
        lines.extend(passes)
    if failures:
        lines.extend(["", "[failures]"])
        lines.extend(failures)
    else:
        lines.extend(["", "[status]", "[OK] inferred prequote contracts passed"])
    return "\n".join(lines) + "\n"


def save_report(text: str, started_at: datetime) -> tuple[Path, Path]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = started_at.strftime("%Y%m%d-%H%M%S")
    latest_path = REPORT_DIR / "latest.txt"
    history_path = REPORT_DIR / f"{stamp}.txt"
    latest_path.write_text(text, encoding="utf-8")
    history_path.write_text(text, encoding="utf-8")
    return latest_path, history_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate inferred prequote reply contracts before rendering.")
    parser.add_argument("--fixture", action="append", help="Fixture path. Repeat to add multiple sources.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--role", action="append", help="Only include fixture roles from eval-sources. Repeatable.")
    parser.add_argument("--exclude-role", action="append", help="Exclude fixture roles from eval-sources. Repeatable.")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--save-report", action="store_true")
    parser.add_argument("--show-passes", action="store_true")
    args = parser.parse_args()

    renderer = load_module("render_prequote_estimate_initial", RENDERER_PATH)
    if args.fixture:
        fixtures = [Path(item) for item in args.fixture]
    elif args.role or args.exclude_role:
        fixtures = load_fixtures_from_config(
            Path(args.config),
            roles=set(args.role or []) or None,
            exclude_roles=set(args.exclude_role or []) or None,
        )
    else:
        fixtures = DEFAULT_FIXTURES
    started_at = datetime.now(JST)
    counters = Counter()
    passes: list[str] = []
    failures: list[str] = []

    for fixture in fixtures:
        cases = renderer.load_cases(fixture)
        if args.limit is not None:
            cases = cases[: args.limit]

        for case in cases:
            if case.get("state") != "prequote":
                counters["skip"] += 1
                continue

            case_id = case.get("case_id") or case.get("id") or "<unknown>"
            key = f"{fixture.name}:{case_id}"
            built = normalize_case(renderer, case)
            errors = generic_checks(case, built)
            errors.extend(expectation_checks(case_id, built))

            if errors:
                counters["fail"] += 1
                failures.extend(f"[NG] {key}: {error}" for error in errors)
                continue

            counters["pass"] += 1
            passes.append(f"[OK] {key}")

    report_text = build_report_text(
        started_at=started_at,
        counters=counters,
        passes=passes if args.show_passes else [],
        failures=failures,
    )

    print(f"pass={counters['pass']} fail={counters['fail']} skip={counters['skip']}")
    if args.save_report:
        latest_path, history_path = save_report(report_text, started_at)
        print(f"report_latest: {latest_path}")
        print(f"report_history: {history_path}")

    if failures:
        for line in failures:
            print(line)
        return 1

    print("[OK] inferred prequote contracts passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
