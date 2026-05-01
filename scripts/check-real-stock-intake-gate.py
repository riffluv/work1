#!/usr/bin/env python3
"""Triage stock/inbox before spending more #RE / xhigh runs.

The gate is intentionally non-mutating: it reads inbox files, classifies each
case into rough families / actions, and reports whether the next useful step is
real-stock promotion, edge triage, contract-packet work, or Pro review.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    import yaml
except ImportError as exc:  # pragma: no cover - operational dependency guard.
    raise SystemExit(f"PyYAML is required: {exc}") from exc


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INBOX = ROOT_DIR / "ops/tests/stock/inbox"
COVERAGE_MAP = ROOT_DIR / "ops/tests/fixture-coverage-map.yaml"
REPORT_DIR = ROOT_DIR / "runtime/regression/coconala-reply/real-stock-intake"
JST = ZoneInfo("Asia/Tokyo")

PHASES = {"prequote", "quote_sent", "purchased", "delivered", "closed"}
PRIVATE_HINTS = {"handoff", "boundary"}
HIGH_RISK_TAGS = {
    "secret_value_pressure",
    "external_work_surface",
    "prepayment_work_pressure",
    "refund_or_free_pressure",
    "success_or_deadline_guarantee_pressure",
    "closed_after_work_boundary",
}
CONTRACT_PACKET_FAMILIES = {
    "purchased_current_status",
    "purchased_commitment_or_deadline_followup",
    "quote_sent_payment_after_share",
    "delivered_light_supplement",
    "closed_relation_check",
}


@dataclass
class StockCase:
    file: Path
    case_id: str
    state: str
    route: str
    service_hint: str
    raw_message: str
    note: str
    user_type: str
    emotional_tone: str


@dataclass
class Triage:
    case: StockCase
    origin: str
    family: str
    action: str
    risk_tags: list[str]
    pro_candidate: bool
    reason: str


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT_DIR))
    except ValueError:
        return str(path)


def as_list(value: object) -> list:
    return value if isinstance(value, list) else []


def parse_text_case_file(path: Path) -> list[StockCase]:
    cases: list[StockCase] = []
    current: dict[str, str] = {}
    with path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n")
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("="):
                continue
            if stripped == "----":
                if current.get("case_id"):
                    cases.append(make_case(path, current))
                current = {}
                continue
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            current[key.strip()] = value.strip()
    if current.get("case_id"):
        cases.append(make_case(path, current))
    return cases


def parse_yaml_case_file(path: Path) -> list[StockCase]:
    data = load_yaml(path)
    cases = []
    for item in as_list(data.get("cases")):
        if item.get("case_id") or item.get("id"):
            cases.append(make_case(path, item))
    return cases


def make_case(path: Path, item: dict) -> StockCase:
    return StockCase(
        file=path,
        case_id=str(item.get("case_id") or item.get("id") or "<missing>"),
        state=str(item.get("state") or "").strip(),
        route=str(item.get("route") or "").strip(),
        service_hint=str(item.get("service_hint") or item.get("service") or "").strip(),
        raw_message=str(item.get("raw_message") or item.get("message") or "").strip(),
        note=str(item.get("note") or "").strip(),
        user_type=str(item.get("user_type") or "").strip(),
        emotional_tone=str(item.get("emotional_tone") or "").strip(),
    )


def load_cases_from_path(path: Path) -> list[StockCase]:
    if path.suffix == ".txt":
        return parse_text_case_file(path)
    if path.suffix in {".yaml", ".yml"}:
        return parse_yaml_case_file(path)
    return []


def source_origin(path: Path) -> str:
    name = path.name.lower()
    if "claude" in name or "gemini" in name or "generated" in name:
        return "generated_supplement"
    if "stock-bulk" in name or "bulk" in name:
        return "synthetic_stock"
    if "shadow" in name or "review" in name:
        return "shadow_review"
    return "real_stock_candidate"


def contains_any(text: str, markers: list[str]) -> bool:
    return any(marker in text for marker in markers)


def detect_risk_tags(case: StockCase) -> list[str]:
    text = f"{case.raw_message}\n{case.note}"
    tags: list[str] = []
    if contains_any(text, [".env", "APIキー", "Webhook secret", "シークレット", "DB接続", "DATABASE_URL", "秘密値"]):
        tags.append("secret_value_pressure")
    if contains_any(text, ["GitHub", "github", "Drive", "Google Drive", "PR", "Issue", "push", "本番反映", "デプロイ", "URL"]):
        tags.append("external_work_surface")
    if contains_any(text, ["支払い前", "購入前", "先に", "原因だけ", "直りそうなら購入", "購入するかはその後"]):
        tags.append("prepayment_work_pressure")
    if contains_any(text, ["返金", "キャンセル", "無料", "無償", "お金", "再度15,000円"]):
        tags.append("refund_or_free_pressure")
    if contains_any(text, ["必ず", "確実", "今日中", "すぐ", "急ぎ", "何日", "納期"]):
        tags.append("success_or_deadline_guarantee_pressure")
    if case.state == "closed" or contains_any(text, ["クローズ", "前回", "旧トークルーム", "おひねり"]):
        tags.append("closed_after_work_boundary")
    if contains_any(text, ["責め", "文句", "苦情", "低評価", "疑って"]):
        tags.append("negative_or_pressure_frame")
    if contains_any(text, ["25,000円", "25000円", "主要1フロー", "引き継ぎ", "handoff"]):
        tags.append("private_or_multi_service_shadow")
    return sorted(set(tags))


def infer_family(case: StockCase, risk_tags: list[str]) -> str:
    text = f"{case.raw_message}\n{case.note}"
    if case.state == "quote_sent":
        if "prepayment_work_pressure" in risk_tags or "external_work_surface" in risk_tags:
            return "quote_sent_prepayment_boundary"
        return "quote_sent_payment_after_share"
    if case.state == "purchased":
        if contains_any(text, ["前に", "18:00", "見通し", "いつ", "まだ", "追加で", "何か送る"]):
            return "purchased_commitment_or_deadline_followup"
        return "purchased_current_status"
    if case.state == "delivered":
        return "delivered_light_supplement"
    if case.state == "closed":
        return "closed_relation_check"
    if case.state == "prequote":
        if case.service_hint in PRIVATE_HINTS or "private_or_multi_service_shadow" in risk_tags:
            return "prequote_private_or_boundary"
        if contains_any(text, ["原因だけ", "調査だけ", "直せた場合", "返金", "キャンセル"]):
            return "prequote_price_scope_or_guarantee"
        if contains_any(text, ["対象", "対応", "見てもらえ", "お願い", "依頼", "相談"]):
            return "prequote_service_fit"
        return "prequote_unknown_or_sparse"
    return "unknown_phase_or_family"


def load_saturated_families() -> set[str]:
    if not COVERAGE_MAP.exists():
        return set()
    data = load_yaml(COVERAGE_MAP)
    result = set()
    for family, item in (data.get("families") or {}).items():
        saturation = item.get("saturation") or {}
        if saturation.get("synthetic_rehearsal") == "high" and item.get("routine_re_status") == "frozen":
            result.add(str(family))
    return result


def choose_action(case: StockCase, origin: str, family: str, risk_tags: list[str], saturated_families: set[str]) -> tuple[str, bool, str]:
    if case.state not in PHASES:
        return "fix_metadata_before_use", True, "state is missing or unknown"
    if case.service_hint in PRIVATE_HINTS or "private_or_multi_service_shadow" in risk_tags:
        return "hold_for_br_or_multi_service_review", False, "private/boundary service hint must not be returned to live #RE"
    if family == "unknown_phase_or_family":
        return "manual_triage_edge", True, "family could not be inferred"
    if origin != "real_stock_candidate":
        if risk_tags and HIGH_RISK_TAGS.intersection(risk_tags):
            return "generated_edge_supplement_only", False, "generated/synthetic high-risk stock can supplement edge, but should not justify routine #RE alone"
        return "generated_supplement_only", False, "not real stock; do not count as release-seal evidence"
    if family in saturated_families:
        return "promote_real_stock_eval_or_edge", False, "synthetic family is saturated, but real stock is still valuable"
    if family in CONTRACT_PACKET_FAMILIES:
        return "add_real_stock_contract_packet_candidate", False, "real stock touches a contract-packet family"
    if risk_tags and HIGH_RISK_TAGS.intersection(risk_tags):
        return "manual_triage_edge", False, "real stock with high-risk tags should go to edge/eval intentionally"
    return "promote_real_stock_eval", False, "real stock candidate for eval coverage"


def triage_case(case: StockCase, saturated_families: set[str]) -> Triage:
    origin = source_origin(case.file)
    risk_tags = detect_risk_tags(case)
    family = infer_family(case, risk_tags)
    action, pro_candidate, reason = choose_action(case, origin, family, risk_tags, saturated_families)
    if "unknown" in family or action == "manual_triage_edge":
        pro_candidate = pro_candidate or origin == "real_stock_candidate"
    return Triage(
        case=case,
        origin=origin,
        family=family,
        action=action,
        risk_tags=risk_tags,
        pro_candidate=pro_candidate,
        reason=reason,
    )


def discover_inbox_files(inbox: Path) -> list[Path]:
    if inbox.is_file():
        return [inbox]
    return sorted(
        path
        for path in inbox.iterdir()
        if path.is_file() and path.name != ".gitkeep" and path.suffix in {".txt", ".yaml", ".yml"}
    )


def build_report_text(
    started_at: datetime,
    inbox: Path,
    triages: list[Triage],
    parse_errors: list[str],
) -> str:
    origin_counts = Counter(item.origin for item in triages)
    action_counts = Counter(item.action for item in triages)
    family_counts = Counter(item.family for item in triages)
    state_counts = Counter(item.case.state or "<missing>" for item in triages)
    pro_candidates = [item for item in triages if item.pro_candidate]
    real_stock_candidates = [item for item in triages if item.origin == "real_stock_candidate"]
    high_value_real = [
        item
        for item in real_stock_candidates
        if item.action in {"promote_real_stock_eval_or_edge", "add_real_stock_contract_packet_candidate", "manual_triage_edge", "promote_real_stock_eval"}
    ]

    hard_fail = bool(parse_errors)
    status_line = "[NG] real stock intake gate failed" if hard_fail else "[OK] real stock intake gate passed"
    if not hard_fail and not real_stock_candidates:
        status_line = "[OK] real stock intake gate passed with no real-stock candidates"

    lines = [
        f"generated_at: {started_at.strftime('%Y-%m-%d %H:%M:%S %Z')}",
        f"inbox: {repo_path(inbox)}",
        f"total_cases: {len(triages)}",
        f"real_stock_candidate_cases: {len(real_stock_candidates)}",
        f"high_value_real_stock_cases: {len(high_value_real)}",
        f"pro_candidate_cases: {len(pro_candidates)}",
        "",
        "[origin_counts]",
    ]
    for key, value in sorted(origin_counts.items()):
        lines.append(f"{key}: {value}")

    lines.extend(["", "[state_counts]"])
    for key, value in sorted(state_counts.items()):
        lines.append(f"{key}: {value}")

    lines.extend(["", "[action_counts]"])
    for key, value in sorted(action_counts.items()):
        lines.append(f"{key}: {value}")

    lines.extend(["", "[family_counts]"])
    for key, value in sorted(family_counts.items()):
        lines.append(f"{key}: {value}")

    if parse_errors:
        lines.extend(["", "[parse_errors]"])
        lines.extend(parse_errors)

    lines.extend(["", "[triage]"])
    for item in triages:
        tags = ",".join(item.risk_tags) if item.risk_tags else "-"
        lines.append(
            f"{item.case.case_id}: file={repo_path(item.case.file)} state={item.case.state or '-'} "
            f"origin={item.origin} family={item.family} action={item.action} "
            f"pro={'yes' if item.pro_candidate else 'no'} tags={tags} reason={item.reason}"
        )

    lines.extend(["", "[decision]"])
    if parse_errors:
        lines.append("next_default: fix_parse_or_metadata_errors_before_triage")
    elif high_value_real:
        lines.append("next_default: promote_selected_real_stock_to_seed_eval_or_edge_then_run_regression")
    elif real_stock_candidates:
        lines.append("next_default: classify_real_stock_candidates_before_more_synthetic_re")
    else:
        lines.append("next_default: wait_for_actual_real_stock_or_use_generated_stock_only_as_supplement")
    lines.append("routine_re: do_not_resume_from_generated_or_saturated_stock_alone")
    lines.append("pro_next: only_for_unknown_real_stock_failure_or_release_seal_review")

    lines.extend(["", "[status]", status_line])
    return "\n".join(lines).rstrip() + "\n"


def build_manifest(triages: list[Triage]) -> dict:
    return {
        "version": 1,
        "generated_at": datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S %Z"),
        "cases": [
            {
                "case_id": item.case.case_id,
                "file": str(item.case.file),
                "state": item.case.state,
                "origin": item.origin,
                "family": item.family,
                "action": item.action,
                "risk_tags": item.risk_tags,
                "pro_candidate": item.pro_candidate,
                "reason": item.reason,
            }
            for item in triages
        ],
    }


def save_report(text: str, triages: list[Triage], started_at: datetime, *, write_manifest: bool) -> tuple[Path, Path, Path | None]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = started_at.strftime("%Y%m%d-%H%M%S")
    latest_path = REPORT_DIR / "latest.txt"
    history_path = REPORT_DIR / f"{stamp}.txt"
    latest_path.write_text(text, encoding="utf-8")
    history_path.write_text(text, encoding="utf-8")
    manifest_path: Path | None = None
    if write_manifest:
        manifest_path = REPORT_DIR / "triage-latest.yaml"
        manifest_path.write_text(yaml.safe_dump(build_manifest(triages), allow_unicode=True, sort_keys=False), encoding="utf-8")
    return latest_path, history_path, manifest_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Triage stock/inbox before promoting real stock or spending #RE/xhigh.")
    parser.add_argument("--inbox", default=str(DEFAULT_INBOX), help="Inbox directory or one stock file.")
    parser.add_argument("--save-report", action="store_true")
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()

    started_at = datetime.now(JST)
    inbox = Path(args.inbox)
    saturated_families = load_saturated_families()
    triages: list[Triage] = []
    parse_errors: list[str] = []

    for path in discover_inbox_files(inbox):
        try:
            cases = load_cases_from_path(path)
        except Exception as exc:  # noqa: BLE001 - report all bad stock files.
            parse_errors.append(f"{repo_path(path)}: {exc}")
            continue
        for case in cases:
            triages.append(triage_case(case, saturated_families))

    report_text = build_report_text(started_at, inbox, triages, parse_errors)
    if args.save_report:
        latest_path, history_path, manifest_path = save_report(
            report_text,
            triages,
            started_at,
            write_manifest=args.write_manifest,
        )
        print(f"report_latest: {latest_path}")
        print(f"report_history: {history_path}")
        if manifest_path:
            print(f"triage_manifest: {manifest_path}")
    print(report_text.rstrip())
    return 1 if parse_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
