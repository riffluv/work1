#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
ESTIMATE_RENDERER = ROOT_DIR / "scripts/render-prequote-estimate-initial.py"
ESTIMATE_LINT = ROOT_DIR / "scripts/check-rendered-prequote-estimate.py"
PURCHASED_RENDERER = ROOT_DIR / "scripts/render-post-purchase-quick.py"
PURCHASED_LINT = ROOT_DIR / "scripts/check-rendered-post-purchase-quick.py"
CLOSED_RENDERER = ROOT_DIR / "scripts/render-closed-followup.py"
CLOSED_LINT = ROOT_DIR / "scripts/check-rendered-closed-followup.py"
DELIVERED_RENDERER = ROOT_DIR / "scripts/render-delivered-followup.py"
DELIVERED_LINT = ROOT_DIR / "scripts/check-rendered-delivered-followup.py"
QUOTE_SENT_RENDERER = ROOT_DIR / "scripts/render-quote-sent-followup.py"
QUOTE_SENT_LINT = ROOT_DIR / "scripts/check-rendered-quote-sent-followup.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_tools() -> dict[str, dict]:
    estimate_renderer = load_module("render_prequote_estimate_initial", ESTIMATE_RENDERER)
    purchased_renderer = load_module("render_post_purchase_quick", PURCHASED_RENDERER)
    closed_renderer = load_module("render_closed_followup", CLOSED_RENDERER)
    delivered_renderer = load_module("render_delivered_followup", DELIVERED_RENDERER)
    quote_sent_renderer = load_module("render_quote_sent_followup", QUOTE_SENT_RENDERER)
    estimate_lint = load_module("check_rendered_prequote_estimate", ESTIMATE_LINT)
    purchased_lint = load_module("check_rendered_post_purchase_quick", PURCHASED_LINT)
    closed_lint = load_module("check_rendered_closed_followup", CLOSED_LINT)
    delivered_lint = load_module("check_rendered_delivered_followup", DELIVERED_LINT)
    quote_sent_lint = load_module("check_rendered_quote_sent_followup", QUOTE_SENT_LINT)

    return {
        "prequote": {
            "renderer": estimate_renderer,
            "lint_module": estimate_lint,
            "render_fn": render_prequote,
            "lint_fn": lambda source: estimate_lint.lint_case(estimate_renderer, source),
        },
        "purchased": {
            "renderer": purchased_renderer,
            "lint_module": purchased_lint,
            "render_fn": render_generic,
            "lint_fn": lambda source: purchased_lint.lint_case(purchased_renderer, source),
        },
        "closed": {
            "renderer": closed_renderer,
            "lint_module": closed_lint,
            "render_fn": render_generic,
            "lint_fn": lambda source: closed_lint.lint_case(closed_renderer, source),
        },
        "delivered": {
            "renderer": delivered_renderer,
            "lint_module": delivered_lint,
            "render_fn": render_generic,
            "lint_fn": lambda source: delivered_lint.lint_case(delivered_renderer, source),
        },
        "quote_sent": {
            "renderer": quote_sent_renderer,
            "lint_module": quote_sent_lint,
            "render_fn": render_generic,
            "lint_fn": lambda source: quote_sent_lint.lint_case(quote_sent_renderer, source),
        },
    }


def render_prequote(renderer, source: dict) -> str:
    normalized = source if source.get("reply_contract") else renderer.build_case_from_source(source)
    return renderer.render_case(normalized)


def render_generic(renderer, source: dict) -> str:
    case = renderer.build_case_from_source(source)
    return renderer.render_case(case)


def choose_lane(case: dict) -> str | None:
    state = case.get("state")
    skeleton = (case.get("reply_stance") or {}).get("reply_skeleton")

    if skeleton == "estimate_initial" and state == "prequote":
        return "prequote"
    if skeleton == "post_purchase_quick" and state == "purchased":
        return "purchased"
    if skeleton == "estimate_followup" and state == "closed":
        return "closed"
    if skeleton == "delivery" and state == "delivered":
        return "delivered"
    if skeleton == "estimate_followup" and state == "quote_sent":
        return "quote_sent"

    if skeleton:
        return None
    if state in {"prequote", "purchased", "closed", "delivered", "quote_sent"}:
        return state
    return None


def format_block(case_id: str, state: str, reply: str) -> str:
    return f"case_id: {case_id}\nstate: {state}\n{reply}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Unified coconala reply renderer for prequote / purchased / closed cases.")
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--case-id")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--lint", action="store_true")
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args()

    tools = load_tools()
    estimate_renderer = tools["prequote"]["renderer"]
    cases = estimate_renderer.load_cases(Path(args.fixture))

    if args.case_id:
        cases = [case for case in cases if case.get("case_id") == args.case_id or case.get("id") == args.case_id]
    if args.limit is not None:
        cases = cases[: args.limit]
    if not cases:
        print("[NG] no cases selected")
        return 1

    rendered_blocks: list[str] = []
    lint_errors: list[str] = []
    save_payload: tuple[str, str] | None = None

    for source in cases:
        state = choose_lane(source)
        case_id = source.get("case_id") or source.get("id") or "<unknown>"
        if state is None:
            lint_errors.append(f"[NG] {case_id}: unsupported state / reply_skeleton combination")
            continue

        tool = tools[state]
        reply = tool["render_fn"](tool["renderer"], source)
        rendered_blocks.append(format_block(case_id, state, reply))

        if args.lint:
            errors = tool["lint_fn"](source)
            lint_errors.extend(f"[NG] {case_id}: {error}" for error in errors)

        if args.save:
            if len(cases) != 1:
                print("[NG] --save requires exactly one case")
                return 1
            save_payload = (reply, source.get("raw_message", ""))

    if save_payload is not None:
        estimate_renderer.save_reply(*save_payload)

    if rendered_blocks:
        print("\n\n----\n\n".join(rendered_blocks))

    if lint_errors:
        print()
        for line in lint_errors:
            print(line)
        return 1

    if args.lint:
        print()
        print(f"[OK] unified reply lint passed: {len(rendered_blocks)} case(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
