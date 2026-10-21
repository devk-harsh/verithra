# Webhook signatures and duplicate deliveries

Locally authored demo manual for the fictional RelayDesk service. Not a public vendor specification.

## Delivery

RelayDesk sends webhook events at least once. Each event has an event_id. Delivery order is not guaranteed. The X-RelayDesk-Signature header is an HMAC-SHA256 digest of the raw request bytes. JSON reserialization changes those bytes and invalidates verification.

## Troubleshooting

Read the raw body before parsing JSON and verify the signature using the endpoint's signing secret. Reject invalid signatures. Persist processed event_id values to ignore duplicate deliveries. Acknowledge valid events quickly with 2xx and process them asynchronously. Do not rely on event arrival order.
