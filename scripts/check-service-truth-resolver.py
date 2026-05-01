#!/usr/bin/env python3
"""Validate service truth resolution for reply runtime.

This gate keeps public reply facts and runtime capability references separated.
It intentionally does not certify every natural-language sentence in service
pages; it checks the fields that can cause public/private, price, scope, or
service-memory drift when the core is later moved into an app.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - operational dependency guard.
    raise SystemExit(f"PyYAML is required: {exc}") from exc


ROOT_DIR = Path(__file__).resolve().parents[1]
SERVICE_REGISTRY = ROOT_DIR / "os/core/service-registry.yaml"


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def as_int_set(values: list[Any]) -> set[int]:
    result: set[int] = set()
    for value in values:
        try:
            result.add(int(value))
        except (TypeError, ValueError):
            continue
    return result


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT_DIR))
    except ValueError:
        return str(path)


def path_from_registry(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else ROOT_DIR / path


def add(items: list[str], service_id: str, message: str) -> None:
    items.append(f"{service_id}: {message}")


def check_service(service: dict[str, Any], *, errors: list[str], warnings: list[str], passes: list[str]) -> None:
    service_id = str(service.get("service_id") or "<missing service_id>")
    public = service.get("public")

    required_path_keys = (
        "source_of_truth",
        "public_facts_file",
        "runtime_capability_file",
        "service_pack_root",
    )
    paths: dict[str, Path] = {}
    for key in required_path_keys:
        path = path_from_registry(service.get(key))
        if path is None:
            add(errors, service_id, f"missing {key}")
            continue
        if not path.exists():
            add(errors, service_id, f"{key} does not exist: {path}")
            continue
        paths[key] = path
        add(passes, service_id, f"{key} exists: {rel(path)}")

    if len(paths) < len(required_path_keys):
        return

    public_facts_path = paths["public_facts_file"]
    runtime_path = paths["runtime_capability_file"]
    pack_facts_path = paths["service_pack_root"] / "facts.yaml"
    if not pack_facts_path.exists():
        add(errors, service_id, f"service_pack_root/facts.yaml missing: {pack_facts_path}")
        return
    if public_facts_path.resolve() != pack_facts_path.resolve():
        add(errors, service_id, "public_facts_file must resolve to service_pack_root/facts.yaml")
    else:
        add(passes, service_id, "public_facts_file is canonical service-pack facts")

    legacy_facts_path = path_from_registry(service.get("facts_file"))
    if legacy_facts_path:
        if legacy_facts_path.resolve() != runtime_path.resolve():
            add(warnings, service_id, "facts_file differs from runtime_capability_file; keep legacy compatibility explicit")
        else:
            add(passes, service_id, "facts_file is runtime_capability_file compatibility alias")

    public_facts = load_yaml(public_facts_path)
    runtime_facts = load_yaml(runtime_path)

    if public_facts.get("service_id") != service_id:
        add(errors, service_id, f"public_facts.service_id mismatch: {public_facts.get('service_id')!r}")
    else:
        add(passes, service_id, "public_facts.service_id matches registry")
    if public_facts.get("public") is not public:
        add(errors, service_id, f"public_facts.public mismatch: {public_facts.get('public')!r} != {public!r}")
    else:
        add(passes, service_id, "public flag matches registry")

    runtime_service_id = runtime_facts.get("service_id")
    declared_facts_service_id = service.get("facts_service_id")
    if runtime_service_id not in {service_id, declared_facts_service_id}:
        add(
            errors,
            service_id,
            "runtime service_id must match registry service_id or explicit facts_service_id "
            f"({runtime_service_id!r})",
        )
    elif runtime_service_id != service_id:
        add(passes, service_id, f"runtime service_id alias is explicit: {runtime_service_id}")
    else:
        add(passes, service_id, "runtime service_id matches registry")

    public_price = (public_facts.get("public_facts") or {}).get("base_price")
    runtime_price = runtime_facts.get("base_price")
    if public_price != runtime_price:
        add(errors, service_id, f"base_price mismatch: public={public_price!r} runtime={runtime_price!r}")
    else:
        add(passes, service_id, f"base_price matches: {public_price}")

    public_addons = [
        value
        for key, value in (public_facts.get("public_facts") or {}).items()
        if str(key).startswith("addon_")
    ]
    runtime_addons = list((runtime_facts.get("addons") or {}).values())
    if as_int_set(public_addons) != as_int_set(runtime_addons):
        add(
            warnings,
            service_id,
            "addon price set differs between public facts and runtime capability "
            f"({public_addons!r} vs {runtime_addons!r})",
        )
    else:
        add(passes, service_id, "addon price set matches")

    public_scope = (public_facts.get("scope_unit") or {}).get("rule")
    runtime_scope = runtime_facts.get("scope_unit")
    if public_scope != runtime_scope:
        add(errors, service_id, f"scope_unit mismatch: public={public_scope!r} runtime={runtime_scope!r}")
    else:
        add(passes, service_id, f"scope_unit matches: {public_scope}")

    source_refs = public_facts.get("source_refs") or {}
    service_page_ref = path_from_registry(source_refs.get("service_page"))
    runtime_ref = path_from_registry(source_refs.get("service_yaml"))
    if service_page_ref and service_page_ref.resolve() != paths["source_of_truth"].resolve():
        add(errors, service_id, "source_refs.service_page differs from registry source_of_truth")
    else:
        add(passes, service_id, "source_refs.service_page traces registry source_of_truth")
    if runtime_ref and runtime_ref.resolve() != runtime_path.resolve():
        add(errors, service_id, "source_refs.service_yaml differs from runtime_capability_file")
    else:
        add(passes, service_id, "source_refs.service_yaml traces runtime_capability_file")

    if public is True:
        public_reply_expectation = (public_facts.get("public_facts") or {}).get("reply_expectation") or {}
        if "initial_reply" in public_reply_expectation:
            add(warnings, service_id, "initial_reply appears in public_facts.reply_expectation for public service")
        internal_expectation = public_facts.get("internal_reply_expectation") or {}
        if internal_expectation.get("initial_reply"):
            add(passes, service_id, "initial_reply is internal_reply_expectation, not public reply fact")


def main() -> int:
    registry = load_yaml(SERVICE_REGISTRY)
    services = as_list(registry.get("services"))
    errors: list[str] = []
    warnings: list[str] = []
    passes: list[str] = []

    if not services:
        errors.append("<registry>: no services found")
    for service in services:
        check_service(service, errors=errors, warnings=warnings, passes=passes)

    for item in passes:
        print(f"[OK] {item}")
    for item in warnings:
        print(f"[WARN] {item}")
    if errors:
        for item in errors:
            print(f"[NG] {item}")
        print(f"[status] FAIL service truth resolver: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1

    status = "with warnings" if warnings else "clean"
    print(f"[status] OK service truth resolver {status}: {len(services)} service(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
