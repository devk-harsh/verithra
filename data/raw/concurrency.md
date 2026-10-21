# Optimistic concurrency and ticket versions

Locally authored demo manual for the fictional RelayDesk service. Not a public vendor specification.

## Conflicting updates

GET /tickets/{id} returns an ETag version. PATCH /tickets/{id} requires If-Match with that version. A 412 PRECONDITION_FAILED means another update changed the ticket. This protects against overwriting someone else's work.

## Troubleshooting

On a 412, fetch the latest ticket and ETag, compare changes, and merge intentionally before retrying PATCH with the new If-Match value. Do not reuse a stale ETag or remove the precondition header. If changes conflict, ask the operator to resolve the conflict rather than silently overwrite data.
