# Environment configuration and startup validation

Locally authored demo manual for the fictional RelayDesk service. Not a public vendor specification.

## Startup

RelayDesk reads RELAYDESK_API_URL and RELAYDESK_WORKSPACE_ID at process startup. RELAYDESK_API_URL must be an absolute HTTPS URL. Changes to environment variables do not update an already running process. Missing required configuration prevents startup.

## Troubleshooting

Set both required environment variables and restart the process after a configuration change. When an old endpoint is still used, inspect the environment of the running service rather than only a terminal shell. Do not commit API credentials to source control or print them in debug logs.
