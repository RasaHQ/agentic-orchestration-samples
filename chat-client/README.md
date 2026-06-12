# Rasa Chat Client

Small local chat UI for the Rasa REST and callback channels.

## Run

Start Rasa with the REST or callback channel enabled, usually from one of the
assistant folders:

```bash
uv run rasa run --enable-api
```

Then start this client from the repository root:

```bash
uv run python chat-client/server.py
```

Open http://127.0.0.1:8282 and send a message.

## REST channel

By default, REST messages are forwarded to:

```text
http://localhost:5005/webhooks/rest/webhook
```

Override that endpoint if needed:

```bash
RASA_REST_URL=http://localhost:5005/webhooks/rest/webhook uv run python chat-client/server.py
```

The client sends:

```json
{"sender": "test_user", "message": "Hi there!"}
```

It accepts either the normal REST response array or a single JSON object response.

## Callback channel

Switch the UI channel selector to `Callback`. The page shows the callback endpoint
that Rasa must be configured to call, for example:

```text
http://127.0.0.1:8282/api/rasa-callback
```

Use that value in the assistant credentials:

```yaml
callback:
  url: "http://127.0.0.1:8282/api/rasa-callback"
```

By default, callback user messages are sent to:

```text
http://localhost:5005/webhooks/callback/webhook
```

Override it if needed:

```bash
RASA_CALLBACK_URL=http://localhost:5005/webhooks/callback/webhook uv run python chat-client/server.py
```

If Rasa runs in Docker Compose, the callback URL shown by the compose service is
the internal Docker URL that the Rasa container can reach.
