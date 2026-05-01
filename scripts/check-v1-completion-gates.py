#!/usr/bin/env python3
"""Aggregate v1 completion gates for the coconala reply OS.

This script does not certify a release as "sealed".  It checks whether the
current bugfix-15000 reply core is still in the v1 completion-candidate zone,
while keeping known gaps visible so routine #RE does not become the default
next step.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    import yaml
except ImportError as exc:  # pragma: no cover - operational dependency guard.
    raise SystemExit(f"PyYAML is required: {exc}") from exc


ROOT_DIR = Path(__file__).resolve().parents[1]
SERVICE_REGISTRY = ROOT_DIR / "os/core/service-registry.yaml"
COVERAGE_MAP = ROOT_DIR / "ops/tests/fixture-coverage-map.yaml"
CORE_CHECKLIST = ROOT_DIR / "docs/reply-quality/core-completion-checklist.ja.md"
COMPLETION_SHELF = ROOT_DIR / "docs/reply-quality/completion-shelf-20260501.ja.md"
REPORT_DIR = ROOT_DIR / "runtime/regression/coconala-reply/v1-completion"
JST = ZoneInfo("Asia/Tokyo")

PUBLIC_SERVICE_ID = "bugfix-15000"
PRIVATE_SERVICE_ID = "handoff-25000"

SATURATED_FAMILIES = {
    "purchased_current_status",
    "quote_sent_payment_after_share",
    "delivered_light_supplement",
    "closed_relation_check",
}
EXPECTED_COVERAGE_GAPS = {
    "real_stock": "low",
    "multi_service": "low",
    "app_memory": "seeded",
    "email_channel": "not_started",
}


@dataclass
class GateResult:
    name: str
    status: str
    summary: str
    details: list[str]
    hard_fail: bool = False


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT_DIR))
    except ValueError:
        return str(path)


def compact_output(output: str, *, max_lines: int = 8) -> list[str]:
    lines = [line.rstrip() for line in output.splitlines() if line.strip()]
    if len(lines) <= max_lines:
        return lines
    head_count = max_lines // 2
    tail_count = max_lines - head_count - 1
    return lines[:head_count] + ["..."] + lines[-tail_count:]


def has_warning(output: str) -> bool:
    if re.search(r"\bWARN(?:ING)?\b", output, flags=re.IGNORECASE):
        return True
    match = re.search(r"\((\d+)\s+warning\(s\)\)", output)
    return bool(match and int(match.group(1)) > 0)


def run_command_gate(name: str, command: list[str], *, show_output: bool) -> GateResult:
    proc = subprocess.run(
        command,
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    output = ((proc.stdout or "") + (proc.stderr or "")).strip()
    details = compact_output(output, max_lines=16 if show_output else 8)
    if proc.returncode != 0:
        return GateResult(
            name=name,
            status="NG",
            summary=f"exit={proc.returncode}",
            details=details,
            hard_fail=True,
        )
    status = "OK_WITH_WARNINGS" if has_warning(output) else "OK"
    return GateResult(
        name=name,
        status=status,
        summary="passed" if status == "OK" else "passed with existing warnings",
        details=details,
    )


def check_required_docs() -> GateResult:
    required_files = [CORE_CHECKLIST, COMPLETION_SHELF, COVERAGE_MAP]
    details: list[str] = []
    failures: list[str] = []
    for path in required_files:
        if path.exists():
            details.append(f"[OK] exists: {repo_path(path)}")
        else:
            failures.append(f"[NG] missing: {repo_path(path)}")

    if not failures:
        checklist = CORE_CHECKLIST.read_text(encoding="utf-8")
        shelf = COMPLETION_SHELF.read_text(encoding="utf-8")
        if "完成判定ゲート" not in checklist:
            failures.append("[NG] core checklist does not mention completion gates")
        else:
            details.append("[OK] core checklist has completion gate section")
        if "v1 完成候補" not in shelf or "機能コア完成圏" not in shelf:
            failures.append("[NG] completion shelf does not state candidate/core-complete position")
        else:
            details.append("[OK] completion shelf states candidate/core-complete position")

    if failures:
        return GateResult(
            name="completion_docs",
            status="NG",
            summary="required completion docs are incomplete",
            details=details + failures,
            hard_fail=True,
        )
    return GateResult(
        name="completion_docs",
        status="OK",
        summary="completion docs present",
        details=details,
    )


def check_service_registry() -> GateResult:
    data = load_yaml(SERVICE_REGISTRY)
    services = {item.get("service_id"): item for item in data.get("services", [])}
    details: list[str] = []
    failures: list[str] = []
    warnings: list[str] = []

    bugfix = services.get(PUBLIC_SERVICE_ID)
    handoff = services.get(PRIVATE_SERVICE_ID)
    if not bugfix:
        failures.append(f"[NG] missing service: {PUBLIC_SERVICE_ID}")
    elif bugfix.get("public") is not True:
        failures.append(f"[NG] {PUBLIC_SERVICE_ID} must be public:true")
    else:
        details.append(f"[OK] {PUBLIC_SERVICE_ID} public:true")

    if not handoff:
        failures.append(f"[NG] missing service: {PRIVATE_SERVICE_ID}")
    elif handoff.get("public") is not False:
        failures.append(f"[NG] {PRIVATE_SERVICE_ID} must remain public:false")
    else:
        details.append(f"[OK] {PRIVATE_SERVICE_ID} public:false")

    for service_id, service in ((PUBLIC_SERVICE_ID, bugfix), (PRIVATE_SERVICE_ID, handoff)):
        if not service:
            continue
        for key in ("source_of_truth", "public_facts_file", "runtime_capability_file", "service_pack_root"):
            value = service.get(key)
            if not value:
                failures.append(f"[NG] {service_id} missing {key}")
                continue
            path = Path(value)
            if not path.exists():
                failures.append(f"[NG] {service_id}.{key} missing path: {path}")
            else:
                details.append(f"[OK] {service_id}.{key}: {repo_path(path)}")

        public_facts = Path(service.get("public_facts_file", ""))
        pack_facts = Path(service.get("service_pack_root", "")) / "facts.yaml"
        if public_facts and pack_facts and public_facts.exists() and pack_facts.exists():
            if public_facts.resolve() != pack_facts.resolve():
                warnings.append(
                    f"[WARN] {service_id}.public_facts_file differs from service_pack_root/facts.yaml"
                )
            else:
                details.append(f"[OK] {service_id}.public_facts_file traces service-pack facts")

    if failures:
        return GateResult(
            name="service_registry",
            status="NG",
            summary="service registry hard failure",
            details=details + warnings + failures,
            hard_fail=True,
        )
    return GateResult(
        name="service_registry",
        status="OK_WITH_WARNINGS" if warnings else "OK",
        summary="registry public/private and trace files are usable",
        details=details + warnings,
    )


def check_coverage_map() -> GateResult:
    data = load_yaml(COVERAGE_MAP)
    families = data.get("families") or {}
    gaps = data.get("coverage_gaps") or {}
    details: list[str] = []
    failures: list[str] = []
    warnings: list[str] = []

    for family in sorted(SATURATED_FAMILIES):
        item = families.get(family)
        if not item:
            failures.append(f"[NG] coverage family missing: {family}")
            continue
        saturation = item.get("saturation") or {}
        if saturation.get("synthetic_rehearsal") != "high":
            failures.append(f"[NG] {family}.synthetic_rehearsal is not high")
        if saturation.get("real_stock") != "low":
            warnings.append(f"[WARN] {family}.real_stock expected low marker for candidate-state tracking")
        if item.get("routine_re_status") != "frozen":
            failures.append(f"[NG] {family}.routine_re_status must be frozen")
        if not item.get("resume_triggers"):
            failures.append(f"[NG] {family}.resume_triggers is empty")
        details.append(
            f"[OK] {family}: synthetic={saturation.get('synthetic_rehearsal')} "
            f"real_stock={saturation.get('real_stock')} routine={item.get('routine_re_status')}"
        )

    for gap, expected_status in EXPECTED_COVERAGE_GAPS.items():
        actual = (gaps.get(gap) or {}).get("status")
        if actual != expected_status:
            failures.append(f"[NG] coverage_gaps.{gap}.status = {actual!r}, expected {expected_status!r}")
        else:
            warnings.append(f"[GAP] {gap}: {actual}")

    if failures:
        return GateResult(
            name="coverage_map",
            status="NG",
            summary="coverage map is not candidate-gate ready",
            details=details + warnings + failures,
            hard_fail=True,
        )
    return GateResult(
        name="coverage_map",
        status="OK_WITH_GAPS",
        summary="synthetic high families are frozen; known gaps remain visible",
        details=details + warnings,
    )


def build_report(
    started_at: datetime,
    results: list[GateResult],
    *,
    deep: bool,
) -> str:
    hard_fail = any(result.hard_fail for result in results)
    known_gaps = [line for result in results for line in result.details if line.startswith("[GAP]")]
    functional_core_complete = not hard_fail
    v1_completion_candidate = not hard_fail
    v1_release_sealed = False

    lines = [
        f"generated_at: {started_at.strftime('%Y-%m-%d %H:%M:%S %Z')}",
        f"service: {PUBLIC_SERVICE_ID}",
        f"classification: {'v1_completion_candidate' if v1_completion_candidate else 'not_candidate'}",
        f"functional_core_complete: {'yes' if functional_core_complete else 'no'}",
        f"v1_completion_candidate: {'yes' if v1_completion_candidate else 'no'}",
        f"v1_release_sealed: {'yes' if v1_release_sealed else 'no'}",
        f"deep_role_suite: {'yes' if deep else 'no'}",
        "",
        "[gates]",
    ]
    for result in results:
        lines.append(f"{result.name}: {result.status} - {result.summary}")

    for result in results:
        lines.extend(["", f"[{result.name}]"])
        lines.extend(result.details or ["<no details>"])

    lines.extend(["", "[known_gaps]"])
    lines.extend(known_gaps or ["<none>"])

    lines.extend(
        [
            "",
            "[decision]",
            "routine_re: stop_for_saturated_families",
            "next_default: real_stock_or_contract_gap_not_more_same_family_re",
            "pro_next: not_now_unless_unknown_failure_or_release_seal_review",
        ]
    )
    if hard_fail:
        lines.extend(["", "[status]", "[NG] v1 completion gate failed"])
    elif known_gaps:
        lines.extend(["", "[status]", "[OK] v1 completion candidate with known gaps"])
    else:
        lines.extend(["", "[status]", "[OK] v1 completion gate passed"])
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
    parser = argparse.ArgumentParser(description="Check v1 completion-candidate gates for the coconala reply OS.")
    parser.add_argument("--deep", action="store_true", help="Also run the full role suite regression.")
    parser.add_argument("--save-report", action="store_true")
    parser.add_argument("--show-output", action="store_true", help="Keep more subprocess output in the report.")
    args = parser.parse_args()

    started_at = datetime.now(JST)
    results: list[GateResult] = [
        check_required_docs(),
        check_service_registry(),
        run_command_gate(
            "service_truth_resolver",
            ["python3", str(ROOT_DIR / "scripts/check-service-truth-resolver.py")],
            show_output=args.show_output,
        ),
        check_coverage_map(),
        run_command_gate(
            "service_pack_fidelity",
            ["python3", str(ROOT_DIR / "scripts/check-service-pack-fidelity.py")],
            show_output=args.show_output,
        ),
        run_command_gate(
            "service_grounding_sentries",
            ["python3", str(ROOT_DIR / "scripts/check-service-grounding-sentries.py")],
            show_output=args.show_output,
        ),
        run_command_gate(
            "contract_packets",
            ["python3", str(ROOT_DIR / "scripts/check-contract-packets.py")],
            show_output=args.show_output,
        ),
        run_command_gate(
            "contract_packet_fixtures",
            ["python3", str(ROOT_DIR / "scripts/check-contract-packet-fixtures.py")],
            show_output=args.show_output,
        ),
        run_command_gate(
            "contract_packet_generated_comparison",
            ["python3", str(ROOT_DIR / "scripts/build-contract-packets.py"), "--check-against-samples", "--save-report"],
            show_output=args.show_output,
        ),
        run_command_gate(
            "contract_packet_writer_brief_sync",
            ["python3", str(ROOT_DIR / "scripts/check-contract-packet-writer-brief-sync.py")],
            show_output=args.show_output,
        ),
        run_command_gate(
            "real_stock_intake",
            ["python3", str(ROOT_DIR / "scripts/check-real-stock-intake-gate.py")],
            show_output=args.show_output,
        ),
    ]
    if args.deep:
        results.append(
            run_command_gate(
                "role_suites",
                ["python3", str(ROOT_DIR / "scripts/check-coconala-reply-role-suites.py")],
                show_output=args.show_output,
            )
        )
    else:
        results.append(
            GateResult(
                name="role_suites",
                status="SKIPPED",
                summary="use --deep for full role suite",
                details=["[SKIP] deep role suite is intentionally not part of the fast candidate gate"],
            )
        )

    report_text = build_report(started_at, results, deep=args.deep)
    if args.save_report:
        latest_path, history_path = save_report(report_text, started_at)
        print(f"report_latest: {latest_path}")
        print(f"report_history: {history_path}")
    print(report_text.rstrip())
    return 1 if any(result.hard_fail for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
