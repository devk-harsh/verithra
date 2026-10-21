# Rate limiting and retry timing

Locally authored demo manual for the fictional RelayDesk service. Not a public vendor specification.

## Throttling

RelayDesk limits each workspace to 60 requests per minute. A 429 response contains Retry-After in seconds. Burst traffic may exhaust the workspace allowance even if one client sends few requests. The limit is shared across clients.

## Troubleshooting

Wait for Retry-After before retrying a 429 response. Add jitter and exponential backoff, capped at 30 seconds, when the header is absent. Use at most three retries for transient failures. Retry mutating requests only with an idempotency key. Investigate all clients sharing the workspace.
