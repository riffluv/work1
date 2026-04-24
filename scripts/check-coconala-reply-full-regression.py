#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT_DIR = Path(__file__).resolve().parents[1]
CONTRACT_CHECKER = ROOT_DIR / "scripts/check-inferred-prequote-contracts.py"
REPLY_REGRESSION = ROOT_DIR / "scripts/check-coconala-reply-regression.py"
SERVICE_PACK_FIDELITY_CHECKER = ROOT_DIR / "scripts/check-service-pack-fidelity.py"
QUOTE_SENT_TEMPLATE_CHECKER = ROOT_DIR / "scripts/check-quote-sent-template-regression.py"
REPLY_MEMORY_CHECKER = ROOT_DIR / "scripts/check-reply-memory-regression.py"
PROJECTION_WARNINGS_CHECKER = ROOT_DIR / "scripts/check-reply-projection-warnings.py"
REPORT_DIR = ROOT_DIR / "runtime/regression/coconala-reply/full"
JST = ZoneInfo("Asia/Tokyo")


def run_command(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, output.strip()


def build_report_text(
    started_at: datetime,
    contract_status: int,
    contract_output: str,
    reply_status: int,
    reply_output: str,
    fidelity_status: int,
    fidelity_output: str,
    template_status: int,
    template_output: str,
    reply_memory_status: int,
    reply_memory_output: str,
    projection_warning_output: str,
) -> str:
    overall_ok = (
        contract_status == 0
        and reply_status == 0
        and fidelity_status == 0
        and template_status == 0
        and reply_memory_status == 0
    )
    lines = [
        f"generated_at: {started_at.strftime('%Y-%m-%d %H:%M:%S %Z')}",
        f"contract_status: {'OK' if contract_status == 0 else 'NG'}",
        f"reply_status: {'OK' if reply_status == 0 else 'NG'}",
        f"service_pack_fidelity_status: {'OK' if fidelity_status == 0 else 'NG'}",
        f"template_status: {'OK' if template_status == 0 else 'NG'}",
        f"reply_memory_status: {'OK' if reply_memory_status == 0 else 'NG'}",
        "",
        "[contract_check]",
        contract_output or "<no output>",
        "",
        "[reply_regression]",
        reply_output or "<no output>",
        "",
        "[service_pack_fidelity]",
        fidelity_output or "<no output>",
        "",
        "[quote_sent_template_regression]",
        template_output or "<no output>",
        "",
        "[reply_memory_regression]",
        reply_memory_output or "<no output>",
        "",
        "[projection_warnings]",
        projection_warning_output or "<no output>",
        "",
        "[status]",
        "[OK] coconala reply full regression passed" if overall_ok else "[NG] coconala reply full regression failed",
    ]
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
    parser = argparse.ArgumentParser(description="Run contract checks and reply regression as one bundle.")
    parser.add_argument("--save-report", action="store_true")
    parser.add_argument("--show-pass-details", action="store_true")
    parser.add_argument("--role", action="append", help="Only include these roles from eval-sources. Repeatable.")
    parser.add_argument("--exclude-role", action="append", help="Exclude these roles from eval-sources. Repeatable.")
    args = parser.parse_args()

    started_at = datetime.now(JST)
    contract_cmd = ["python3", str(CONTRACT_CHECKER)]
    reply_cmd = ["python3", str(REPLY_REGRESSION)]
    fidelity_cmd = ["python3", str(SERVICE_PACK_FIDELITY_CHECKER)]
    template_cmd = ["python3", str(QUOTE_SENT_TEMPLATE_CHECKER)]
    reply_memory_cmd = ["python3", str(REPLY_MEMORY_CHECKER)]
    projection_warning_cmd = ["python3", str(PROJECTION_WARNINGS_CHECKER)]
    if args.show_pass_details:
        contract_cmd.append("--show-passes")
        reply_cmd.append("--show-passes")
        fidelity_cmd.append("--show-passes")
    for role in args.role or []:
        contract_cmd.extend(["--role", role])
        reply_cmd.extend(["--role", role])
        fidelity_cmd.extend(["--role", role])
        projection_warning_cmd.extend(["--role", role])
    for role in args.exclude_role or []:
        contract_cmd.extend(["--exclude-role", role])
        reply_cmd.extend(["--exclude-role", role])
        fidelity_cmd.extend(["--exclude-role", role])
        projection_warning_cmd.extend(["--exclude-role", role])

    contract_status, contract_output = run_command(contract_cmd)
    reply_status, reply_output = run_command(reply_cmd)
    fidelity_status, fidelity_output = run_command(fidelity_cmd)
    template_status, template_output = run_command(template_cmd)
    reply_memory_status, reply_memory_output = run_command(reply_memory_cmd)
    _projection_warning_status, projection_warning_output = run_command(projection_warning_cmd)

    report_text = build_report_text(
        started_at=started_at,
        contract_status=contract_status,
        contract_output=contract_output,
        reply_status=reply_status,
        reply_output=reply_output,
        fidelity_status=fidelity_status,
        fidelity_output=fidelity_output,
        template_status=template_status,
        template_output=template_output,
        reply_memory_status=reply_memory_status,
        reply_memory_output=reply_memory_output,
        projection_warning_output=projection_warning_output,
    )

    if args.save_report:
        latest_path, history_path = save_report(report_text, started_at)
        print(f"report_latest: {latest_path}")
        print(f"report_history: {history_path}")

    print(report_text.rstrip())
    if contract_status != 0 or reply_status != 0 or fidelity_status != 0 or template_status != 0 or reply_memory_status != 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
