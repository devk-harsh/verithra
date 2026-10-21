# Authorization and role scopes

Locally authored demo manual for the fictional RelayDesk service. Not a public vendor specification.

## Roles

A valid token does not grant every permission. A 403 with code SCOPE_MISSING means the account lacks the route's required scope. The reader role can read tickets but cannot close them. The operator role can close tickets. Permissions are enforced on the server.

## Troubleshooting

Check the required scope and the account role when closing a ticket returns 403. Ask a workspace administrator to grant the operator role when appropriate. Acquire a fresh access token after a role change; old tokens retain old scope claims until expiry. Do not disable authorization checks.
