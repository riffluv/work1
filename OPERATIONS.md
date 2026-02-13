# OPERATIONS.md

## Goal
Use this workspace continuously for all client work.
Do not create a brand-new workspace for each case.

## Core Rule
- Keep shared operating docs at workspace root.
- Keep client-specific artifacts inside each case folder only.

## Folder Policy
- Root (`/work`): operating rules, templates, scripts, shared references.
- `cases/ACTIVE/*`: active client cases.
- `cases/HOLD/*`: waiting for client input/payment/scope decision.
- `cases/CLOSED/*`: completed cases.

## What belongs in case folders
- intake notes
- source files from client
- working patch files
- deliverables
- case-specific logs

## What should NOT go into case folders
- global agent instructions
- global templates
- long strategy docs for all services
- reusable scripts

## Naming Convention
- `YYYYMMDD-client-or-platform-topic`
- Example: `20260210-coconala-stripe-webhook-fix`

## Lifecycle
1. Create case in `cases/ACTIVE`
2. Work and deliver
3. Move to `cases/HOLD` if blocked
4. Move to `cases/CLOSED` after completion

## AI Context Strategy
- Always open this same `/work` workspace.
- Keep AGENTS/CLAUDE at root so every new task inherits base rules.
- Use per-case README to avoid re-explaining project facts.
