# Gateway timeouts and slow downstream services

Locally authored demo manual for the fictional RelayDesk service. Not a public vendor specification.

## Latency

The RelayDesk gateway waits 10 seconds for an upstream response. A 504 indicates this timeout elapsed. A client socket timeout does not prove a write failed: the operation may have committed before the response was lost. Requests carry X-Request-ID for tracing.

## Troubleshooting

Find X-Request-ID in gateway and worker logs to identify the slow dependency. Move work longer than 10 seconds to a queued operation and return 202 with a job ID. For ticket writes, retry only with the original Idempotency-Key. Avoid blindly raising timeouts or repeating writes with new keys.
