# Idempotent ticket creation

Locally authored demo manual for the fictional RelayDesk service. Not a public vendor specification.

## Duplicate requests

POST /tickets accepts Idempotency-Key. A key is scoped to a workspace and retained for 24 hours. Replaying an identical payload with the same key returns the original ticket. Reusing the key with a different payload returns 409 IDEMPOTENCY_CONFLICT.

## Troubleshooting

Generate one UUID key per intended ticket creation and reuse it across retries, including network timeouts. Never generate a fresh key for every retry. If a 409 IDEMPOTENCY_CONFLICT occurs, compare the original payload; use a new key only for a genuinely different operation. After 24 hours do not assume deduplication remains.
