# code and writing conventions
- Customer-facing communication is Japanese and must be concise, natural, and copy-safe (no unnecessary leading spaces at line starts).
- For code comments, default to the rules in `docs/code-comment-style.ja.md`: short, concrete, natural wording; avoid AI-sounding comments; match the repository language policy and avoid increasing mixed-language comments.
- Operational decisions must be based on evidence first: logs, code, env var names, reproduction steps.
- Before proposing fixes, confirm expected behavior, actual behavior, environment, and when implementing gather the required five items: expected behavior, actual behavior, reproduction steps, error logs, stack/runtime/deployment target.
- Scope control is strict: do not expand scope unintentionally; explicitly distinguish same cause vs separate cause.
- Stripe instructions should use Japanese dashboard UI names first and distinguish Checkout vs Billing Portal, `prod_...` vs `price_...`.
- For replies, use skills when drafting customer text. Default chain for bugfix replies: `coconala-reply-bugfix-ja` then `japanese-chat-natural-ja`.
- Persist sendable reply text into `返信文_latest.txt`.
- Keep edits reversible and documented; do not handle secrets in chat or artifacts.