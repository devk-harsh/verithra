# Authentication and expired credentials

Locally authored demo manual for the fictional RelayDesk service. Not a public vendor specification.

## Tokens

RelayDesk accepts Authorization: Bearer <access_token> on protected routes. Access tokens expire after 15 minutes. A 401 with code TOKEN_EXPIRED means the token is expired; a 401 with TOKEN_INVALID means the signature or issuer is invalid. Never log raw credentials.

## Troubleshooting

For TOKEN_EXPIRED, obtain a new access token using POST /auth/refresh and retry the original request once. Refresh tokens are single-use and rotate on every refresh. Serialize refresh attempts per browser session. If refresh returns 401, sign in again instead of retrying forever.
