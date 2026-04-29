#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml


ROOT_DIR = Path(__file__).resolve().parents[1]
SERVICE_REGISTRY = ROOT_DIR / "os/core/service-registry.yaml"
REPORT_DIR = ROOT_DIR / "runtime/regression/service-grounding-sentries"
JST = ZoneInfo("Asia/Tokyo")

PUBLIC_BUGFIX_SERVICE_ID = "bugfix-15000"
BUGFIX_SEMANTIC_FIXTURE = ROOT_DIR / "ops/tests/quality-cases/active/public-launch-practical-bugfix44.yaml"
LIVE_SHADOW_FIXTURES = [
    ROOT_DIR / "ops/tests/quality-cases/active/public-private-leakage-bugfix39.yaml",
    ROOT_DIR / "ops/tests/quality-cases/active/post-br-live-boundary-bugfix41.yaml",
    ROOT_DIR / "ops/tests/quality-cases/active/post-docs-cleanup-noise-bugfix42.yaml",
    ROOT_DIR / "ops/tests/quality-cases/active/live-core-human-review-bugfix43.yaml",
    ROOT_DIR / "ops/tests/quality-cases/active/public-launch-practical-bugfix44.yaml",
    ROOT_DIR / "ops/tests/quality-cases/active/post-pro-grounding-bugfix45.yaml",
    ROOT_DIR / "ops/tests/quality-cases/active/post-pro-review-lenses-bugfix46.yaml",
]
RENDERER_FILES = [
    ROOT_DIR / "scripts/render-prequote-estimate-initial.py",
    ROOT_DIR / "scripts/render-quote-sent-followup.py",
    ROOT_DIR / "scripts/render-post-purchase-quick.py",
    ROOT_DIR / "scripts/render-delivered-followup.py",
    ROOT_DIR / "scripts/render-closed-followup.py",
]
PUBLIC_FALSE_SHADOW_MARKERS = [
    "handoff-25000",
    "25,000円",
    "25000円",
    "25,000円側",
    "主要1フロー",
    "主要な処理の流れ1つ",
    "引き継ぎメモ",
]
PUBLIC_PRICE_MARKERS = ["15,000円", "15000円"]


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def text_has_all(text: str, markers: list[str]) -> bool:
    return all(marker in text for marker in markers)


def text_has_any(text: str, markers: list[str]) -> bool:
    return any(marker in text for marker in markers)


def flatten_strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(flatten_strings(item))
        return result
    if isinstance(value, dict):
        result = []
        for item in value.values():
            result.extend(flatten_strings(item))
        return result
    return []


def load_registry_service(service_id: str) -> dict:
    registry = load_yaml(SERVICE_REGISTRY)
    for service in registry.get("services") or []:
        if service.get("service_id") == service_id:
            return service
    raise KeyError(f"service not found: {service_id}")


def run_renderer(fixture: Path) -> tuple[int, str]:
    proc = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/render-coconala-reply.py"), "--fixture", str(fixture), "--lint"],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
    )
    return proc.returncode, ((proc.stdout or "") + (proc.stderr or "")).strip()


def check_semantic_smoke() -> tuple[list[str], list[str], list[str]]:
    service = load_registry_service(PUBLIC_BUGFIX_SERVICE_ID)
    page_text = Path(service["source_of_truth"]).read_text(encoding="utf-8")
    service_yaml = load_yaml(Path(service["facts_file"]))
    pack_facts = load_yaml(Path(service["service_pack_root"]) / "facts.yaml")
    pack_text = "\n".join(flatten_strings(pack_facts))
    service_text = "\n".join(flatten_strings(service_yaml))

    render_status, rendered = run_renderer(BUGFIX_SEMANTIC_FIXTURE)
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []
    if render_status != 0:
        failures.append(f"[NG] semantic_smoke: renderer failed for {BUGFIX_SEMANTIC_FIXTURE}")
        failures.append(rendered)
        return passes, warnings, failures

    checks = [
        (
            "base_price_15000",
            [
                ("service_page", "15,000円" in page_text),
                ("service_yaml", service_yaml.get("base_price") == 15000),
                ("service_pack", (pack_facts.get("public_facts") or {}).get("base_price") == 15000),
                ("rendered_reply", "15,000円" in rendered),
            ],
        ),
        (
            "scope_unit_one_bug_same_cause",
            [
                ("service_page", text_has_all(page_text, ["不具合1件", "同一原因"])),
                ("service_yaml", service_yaml.get("scope_unit") == "same_cause_and_same_flow_and_same_endpoint"),
                ("service_pack", ((pack_facts.get("scope_unit") or {}).get("rule") == "same_cause_and_same_flow_and_same_endpoint")),
                ("rendered_reply", text_has_any(rendered, ["不具合1件", "同じ原因", "同一原因", "15,000円内"])),
            ],
        ),
        (
            "fixed_file_return_deliverable",
            [
                ("service_page", "修正済みファイル" in page_text),
                ("service_yaml", "fixed_zip_or_patch" in (service_yaml.get("deliverables") or [])),
                ("service_pack", "修正済みファイル" in pack_text),
                ("rendered_reply", "修正済みファイル" in rendered),
            ],
        ),
        (
            "raw_secret_values_are_not_required",
            [
                ("service_page", text_has_all(page_text, [".env", "キー名"]) and text_has_any(page_text, ["秘密値", "値は送ら", "値の共有は不要"])),
                ("service_yaml", "raw_secret_values" in (service_yaml.get("hard_no") or [])),
                ("service_pack", text_has_any(pack_text, ["キー名", "secrets", "raw_secret_values"])),
                ("rendered_reply", text_has_all(rendered, ["値そのもの", "送ら"])),
            ],
        ),
        (
            "diagnosis_only_pressure_is_blocked",
            [
                ("service_page", text_has_all(page_text, ["原因の確認", "修正済みファイル"])),
                ("service_yaml", "調査時間だけの料金ではなく" in ((service_yaml.get("bugfix_fee_policy") or {}).get("buyer_facing_rule") or "")),
                ("service_pack", text_has_any(pack_text, ["原因確認", "修正済みファイル"])),
                ("rendered_reply", text_has_all(rendered, ["原因だけ", "診断する形ではありません"])),
            ],
        ),
        (
            "extra_work_requires_prior_consultation",
            [
                ("service_page", text_has_all(page_text, ["進める前", "費用"])),
                ("service_yaml", bool((service_yaml.get("bugfix_fee_policy") or {}).get("extra_fee_requires_prior_consultation"))),
                ("service_pack", text_has_any(pack_text, ["追加料金", "先に", "相談"])),
                ("rendered_reply", text_has_all(rendered, ["進める前", "対応方法と費用"])),
            ],
        ),
    ]

    for check_id, parts in checks:
        missing = [name for name, ok in parts if not ok]
        if missing:
            failures.append(f"[NG] semantic_smoke:{check_id}: missing {', '.join(missing)}")
        else:
            passes.append(f"[OK] semantic_smoke:{check_id}")

    registry_pack_id = (pack_facts.get("service_id") or "").strip()
    registry_service_id = (service.get("service_id") or "").strip()
    facts_service_id = (service_yaml.get("service_id") or "").strip()
    declared_facts_service_id = (service.get("facts_service_id") or "").strip()
    if facts_service_id and facts_service_id != registry_service_id:
        if declared_facts_service_id == facts_service_id:
            passes.append(
                "[OK] semantic_smoke: registry facts_service_id alias is explicit "
                f"({registry_service_id} -> {facts_service_id})"
            )
        else:
            warnings.append(
                "[WARN] semantic_smoke: facts_file service_id differs from registry "
                f"({facts_service_id} != {registry_service_id}); keep alias explicit before adding more services"
            )
    if registry_pack_id and registry_pack_id != registry_service_id:
        failures.append(
            f"[NG] semantic_smoke: service-pack facts service_id mismatch ({registry_pack_id} != {registry_service_id})"
        )
    return passes, warnings, failures


def scan_renderer_literals() -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    passes: list[str] = []
    public_price_counter: Counter[str] = Counter()
    shadow_counter: Counter[str] = Counter()
    public_price_samples: list[str] = []
    shadow_samples: list[str] = []

    for path in RENDERER_FILES:
        if not path.exists():
            continue
        rel = path.relative_to(ROOT_DIR)
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for marker in PUBLIC_PRICE_MARKERS:
                if marker in line:
                    public_price_counter[str(rel)] += 1
                    if len(public_price_samples) < 12:
                        public_price_samples.append(f"{rel}:{lineno}: {marker}")
            for marker in PUBLIC_FALSE_SHADOW_MARKERS:
                if marker in line:
                    shadow_counter[str(rel)] += 1
                    if len(shadow_samples) < 12:
                        shadow_samples.append(f"{rel}:{lineno}: {marker}")

    if public_price_counter:
        total = sum(public_price_counter.values())
        warnings.append(
            "[WARN] renderer_literal_drift_scan: "
            f"{total} public price literal(s) found in renderer code; currently allowed but second-source risk"
        )
        warnings.extend(f"[WARN] renderer_literal_drift_scan sample: {sample}" for sample in public_price_samples)
    else:
        passes.append("[OK] renderer_literal_drift_scan: no public price literals found")

    if shadow_counter:
        total = sum(shadow_counter.values())
        warnings.append(
            "[WARN] renderer_literal_drift_scan: "
            f"{total} private/shadow lexeme literal(s) found in renderer code; live sentry must remain green"
        )
        warnings.extend(f"[WARN] renderer_literal_drift_scan sample: {sample}" for sample in shadow_samples)
    else:
        passes.append("[OK] renderer_literal_drift_scan: no private/shadow lexemes found in renderer code")

    return passes, warnings


def check_live_shadow_leak() -> tuple[list[str], list[str]]:
    passes: list[str] = []
    failures: list[str] = []
    for fixture in LIVE_SHADOW_FIXTURES:
        status, rendered = run_renderer(fixture)
        label = fixture.relative_to(ROOT_DIR)
        if status != 0:
            failures.append(f"[NG] public_false_shadow_lexeme:{label}: renderer/lint failed")
            failures.append(rendered)
            continue
        leaked = [marker for marker in PUBLIC_FALSE_SHADOW_MARKERS if marker in rendered]
        if leaked:
            failures.append(f"[NG] public_false_shadow_lexeme:{label}: leaked {', '.join(leaked)}")
        else:
            passes.append(f"[OK] public_false_shadow_lexeme:{label}")
    return passes, failures


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
        lines.append("[NG] service grounding sentries failed")
    elif warnings:
        lines.append("[OK] service grounding sentries passed with warnings")
    else:
        lines.append("[OK] service grounding sentries passed")
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
    parser = argparse.ArgumentParser(description="Run service grounding sentries for reply OS.")
    parser.add_argument("--save-report", action="store_true")
    parser.add_argument("--fail-on-warnings", action="store_true")
    args = parser.parse_args()

    started_at = datetime.now(JST)
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    semantic_passes, semantic_warnings, semantic_failures = check_semantic_smoke()
    literal_passes, literal_warnings = scan_renderer_literals()
    leak_passes, leak_failures = check_live_shadow_leak()

    passes.extend(semantic_passes)
    passes.extend(literal_passes)
    passes.extend(leak_passes)
    warnings.extend(semantic_warnings)
    warnings.extend(literal_warnings)
    failures.extend(semantic_failures)
    failures.extend(leak_failures)
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
