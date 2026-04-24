#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT_DIR / "ops/tests/eval-sources.yaml"
SERVICE_REGISTRY = ROOT_DIR / "os/core/service-registry.yaml"
REPORT_DIR = ROOT_DIR / "runtime/regression/service-pack-fidelity"
DEFAULT_ROLE = "regression_seed"
JST = ZoneInfo("Asia/Tokyo")

SERVICE_ID_FALLBACK = {
    "service_pack_fidelity_bugfix": "bugfix-15000",
    "service_pack_fidelity_handoff": "handoff-25000",
}
ALLOWED_FIDELITY_FILES = {
    "facts",
    "boundaries",
    "decision-contract",
    "evidence-contract",
    "routing-playbooks",
    "state-schema",
}
RUNTIME_ASSET_FILES = {"seeds", "tone-profile"}
IMPLICIT_ROOT_KEYS = {
    "routing-playbooks": "playbooks",
    "state-schema": "thread_state",
}


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_active_sources(
    config_path: Path,
    roles: set[str] | None = None,
    exclude_roles: set[str] | None = None,
) -> list[dict]:
    data = load_yaml(config_path)
    sources: list[dict] = []
    for bucket in ("primary_sources", "secondary_sources"):
        for item in data.get(bucket, []):
            if item.get("status") != "active":
                continue
            role = item.get("role")
            if roles and role not in roles:
                continue
            if exclude_roles and role in exclude_roles:
                continue
            sources.append(item)
    return sources


def is_fidelity_source(path: Path) -> bool:
    if path.suffix not in {".yaml", ".yml"}:
        return False
    try:
        payload = load_yaml(path)
    except yaml.YAMLError:
        return False
    if payload.get("kind") == "service_pack_fidelity_regression":
        return True
    if path.parent.name in SERVICE_ID_FALLBACK and isinstance(payload.get("cases"), list):
        return True
    return False


def load_registry_index() -> dict[str, dict]:
    data = load_yaml(SERVICE_REGISTRY)
    return {item["service_id"]: item for item in data.get("services", [])}


def source_label(path: Path) -> str:
    return f"{path.parent.name}/{path.name}"


def derive_service_id(source_path: Path, payload: dict) -> str:
    service_id = payload.get("service_id")
    if service_id:
        return service_id
    fallback = SERVICE_ID_FALLBACK.get(source_path.parent.name)
    if fallback:
        return fallback
    raise KeyError(f"service_id is missing and no fallback exists for {source_path}")


def load_service_pack(pack_root: Path) -> dict[str, dict]:
    pack: dict[str, dict] = {}
    for name in (
        "facts",
        "boundaries",
        "decision-contract",
        "evidence-contract",
        "routing-playbooks",
        "state-schema",
        "seeds",
        "tone-profile",
    ):
        path = pack_root / f"{name}.yaml"
        if path.exists():
            pack[name] = load_yaml(path)
    return pack


def resolve_ref(pack: dict[str, dict], ref: str) -> tuple[bool, str]:
    if not ref:
        return False, "empty ref"

    parts = ref.split(".")
    file_key = parts[0]
    if file_key in RUNTIME_ASSET_FILES:
        return False, f"{file_key} is a runtime asset and not allowed for semantic fidelity"
    if file_key not in ALLOWED_FIDELITY_FILES:
        return False, f"{file_key} is not an allowed fidelity layer"
    if file_key not in pack:
        return False, f"{file_key}.yaml not found"

    current = pack[file_key]
    implicit_root = IMPLICIT_ROOT_KEYS.get(file_key)
    if implicit_root and isinstance(current, dict) and implicit_root in current:
        first_segment = parts[1] if len(parts) > 1 else None
        if first_segment and first_segment not in current:
            current = current[implicit_root]

    for segment in parts[1:]:
        if isinstance(current, dict):
            if segment not in current:
                return False, f"missing key: {segment}"
            current = current[segment]
            continue
        if isinstance(current, list):
            if not segment.isdigit():
                return False, f"list index required at: {segment}"
            index = int(segment)
            if index >= len(current):
                return False, f"list index out of range: {segment}"
            current = current[index]
            continue
        return False, f"cannot descend into scalar at: {segment}"
    return True, "ok"


def build_report_text(
    started_at: datetime,
    source_counters: dict[str, Counter],
    passes: list[str],
    failures: list[str],
    show_passes: bool,
) -> str:
    total_pass = sum(counter["pass"] for counter in source_counters.values())
    total_fail = sum(counter["fail"] for counter in source_counters.values())
    lines = [
        f"generated_at: {started_at.strftime('%Y-%m-%d %H:%M:%S %Z')}",
        f"total_pass: {total_pass}",
        f"total_fail: {total_fail}",
        "",
        "[sources]",
    ]
    for label, counter in source_counters.items():
        lines.append(f"{label}: pass={counter['pass']} fail={counter['fail']}")

    if show_passes and passes:
        lines.extend(["", "[passes]"])
        lines.extend(passes)

    if failures:
        lines.extend(["", "[failures]"])
        lines.extend(failures)
        lines.extend(["", "[status]", "[NG] service-pack fidelity regression failed"])
    else:
        lines.extend(["", "[status]", "[OK] service-pack fidelity regression passed"])
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
    parser = argparse.ArgumentParser(description="Check service-pack fidelity cases against live service-pack files.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--source", action="append", help="Run a specific cases.yaml file. Repeatable.")
    parser.add_argument("--role", action="append", help="Only include these roles from eval-sources. Repeatable.")
    parser.add_argument("--exclude-role", action="append", help="Exclude these roles from eval-sources. Repeatable.")
    parser.add_argument("--show-passes", action="store_true")
    parser.add_argument("--save-report", action="store_true")
    args = parser.parse_args()

    started_at = datetime.now(JST)
    registry = load_registry_index()

    if args.source:
        source_paths = [Path(item) for item in args.source]
    else:
        roles = set(args.role or [])
        if not roles:
            roles = {DEFAULT_ROLE}
        exclude_roles = set(args.exclude_role or [])
        sources = load_active_sources(Path(args.config), roles=roles or None, exclude_roles=exclude_roles or None)
        source_paths = [Path(item["path"]) for item in sources if is_fidelity_source(Path(item["path"]))]

    if not source_paths:
        print("[OK] no service-pack fidelity sources selected")
        return 0

    source_counters: dict[str, Counter] = {}
    passes: list[str] = []
    failures: list[str] = []

    for source_path in source_paths:
        payload = load_yaml(source_path)
        label = source_label(source_path)
        counter = Counter()
        source_counters[label] = counter

        service_id = derive_service_id(source_path, payload)
        service = registry.get(service_id)
        if service is None:
            counter["fail"] += 1
            failures.append(f"[NG] {label}: unknown service_id {service_id}")
            continue

        pack_root = Path(service["service_pack_root"])
        if not pack_root.exists():
            counter["fail"] += 1
            failures.append(f"[NG] {label}: service_pack_root missing: {pack_root}")
            continue

        if not Path(service["source_of_truth"]).exists():
            counter["fail"] += 1
            failures.append(f"[NG] {label}: source_of_truth missing: {service['source_of_truth']}")
            continue

        pack = load_service_pack(pack_root)
        cases = payload.get("cases") or []
        if not cases:
            counter["fail"] += 1
            failures.append(f"[NG] {label}: cases missing")
            continue

        for case in cases:
            case_id = case.get("case_id") or case.get("id") or "<unknown>"
            expected_refs = case.get("expected_contract_refs") or []
            if not expected_refs:
                counter["fail"] += 1
                failures.append(f"[NG] {label}:{case_id}: expected_contract_refs missing")
                continue

            missing_reasons: list[str] = []
            for ref in expected_refs:
                ok, reason = resolve_ref(pack, ref)
                if not ok:
                    missing_reasons.append(f"{ref} ({reason})")

            if missing_reasons:
                counter["fail"] += 1
                clause = case.get("public_clause_summary") or case.get("source_summary") or ""
                suffix = f" | clause={clause}" if clause else ""
                failures.append(f"[NG] {label}:{case_id}: " + "; ".join(missing_reasons) + suffix)
                continue

            counter["pass"] += 1
            if args.show_passes:
                passes.append(f"[OK] {label}:{case_id}")

    report_text = build_report_text(started_at, source_counters, passes, failures, args.show_passes)
    if args.save_report:
        latest_path, history_path = save_report(report_text, started_at)
        print(f"report_latest: {latest_path}")
        print(f"report_history: {history_path}")
    print(report_text.rstrip())
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
