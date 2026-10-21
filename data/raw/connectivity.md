# TLS and DNS connection failures

Locally authored demo manual for the fictional RelayDesk service. Not a public vendor specification.

## Transport

A DNS resolution failure happens before an HTTP response. A certificate verification error indicates a TLS trust or hostname problem. Neither error is an HTTP authentication failure. RelayDesk requires valid TLS certificates and hostnames.

## Troubleshooting

For DNS failures, verify the configured hostname and resolver connectivity. For certificate errors, verify the hostname, system clock and trusted CA bundle. Configure the approved corporate CA when an authorized TLS proxy is used. Do not disable certificate verification as a workaround.
