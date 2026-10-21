# Queued jobs and worker health

Locally authored demo manual for the fictional RelayDesk service. Not a public vendor specification.

## Asynchronous jobs

POST /exports returns 202 and a job_id. Jobs move through queued, running, succeeded or failed. A queued job needs a healthy worker subscribed to the same workspace queue. A worker heartbeat older than 60 seconds is stale. API availability alone does not imply worker health.

## Troubleshooting

When exports remain queued, check worker heartbeats and workspace queue subscriptions. Start or restart the missing worker and inspect worker logs for startup errors. Poll GET /jobs/{job_id} with backoff until succeeded or failed. Use the returned failure reason; do not poll without a time limit.
