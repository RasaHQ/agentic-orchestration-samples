from __future__ import annotations

import json
import os
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, urlparse
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


HOST = os.environ.get("CHAT_CLIENT_HOST", "127.0.0.1")
PORT = int(os.environ.get("CHAT_CLIENT_PORT", "8282"))
RASA_REST_URL = os.environ.get(
    "RASA_REST_URL",
    "http://localhost:5005/webhooks/rest/webhook",
)
RASA_CALLBACK_URL = os.environ.get(
    "RASA_CALLBACK_URL",
    "http://localhost:5005/webhooks/callback/webhook",
)
RASA_API_URL = os.environ.get("RASA_API_URL", "http://localhost:5005").rstrip("/")
PUBLIC_BASE_URL = os.environ.get(
    "CHAT_CLIENT_PUBLIC_URL",
    f"http://{'127.0.0.1' if HOST == '0.0.0.0' else HOST}:{PORT}",
).rstrip("/")
CALLBACK_ENDPOINT = f"{PUBLIC_BASE_URL}/api/rasa-callback"
STATIC_DIR = Path(__file__).resolve().parent
CALLBACK_MESSAGES: list[dict[str, Any]] = []
CALLBACK_LOCK = threading.Lock()
NEXT_CALLBACK_MESSAGE_ID = 0


class ChatClientHandler(BaseHTTPRequestHandler):
    server_version = "RasaChatClient/0.1"

    def do_GET(self) -> None:
        parsed_path = urlparse(self.path)

        if parsed_path.path in {"/", "/index.html"}:
            self._send_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
            return

        if parsed_path.path == "/api/config":
            self._send_json(
                HTTPStatus.OK,
                {
                    "rest_url": RASA_REST_URL,
                    "callback_url": RASA_CALLBACK_URL,
                    "rasa_api_url": RASA_API_URL,
                    "callback_endpoint": CALLBACK_ENDPOINT,
                },
            )
            return

        if parsed_path.path == "/api/callback-messages":
            try:
                query = parse_qs(parsed_path.query)
                sender = query.get("sender", [""])[0]
                after = int(query.get("after", ["0"])[0] or "0")
            except ValueError:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "after must be an integer."})
                return
            self._send_json(
                HTTPStatus.OK,
                {
                    "messages": self._callback_messages(sender=sender, after=after),
                },
            )
            return

        if parsed_path.path == "/api/tracker":
            query = parse_qs(parsed_path.query)
            sender = query.get("sender", [""])[0].strip()
            if not sender:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "sender is required."})
                return

            try:
                tracker = self._fetch_tracker(sender=sender)
                self._send_json(HTTPStatus.OK, {"tracker": tracker})
            except RuntimeError as exc:
                self._send_json(HTTPStatus.BAD_GATEWAY, {"error": str(exc)})
            return

        self._send_json(
            HTTPStatus.NOT_FOUND,
            {"error": "Not found"},
        )

    def do_POST(self) -> None:
        parsed_path = urlparse(self.path)

        if parsed_path.path == "/api/rasa-callback":
            try:
                payload = self._read_json()
                messages = payload if isinstance(payload, list) else [payload]
                stored_messages = self._store_callback_messages(messages)
                self._send_json(
                    HTTPStatus.OK,
                    {"stored": len(stored_messages), "messages": stored_messages},
                )
            except ValueError as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return

        if parsed_path.path != "/api/message":
            self._send_json(
                HTTPStatus.NOT_FOUND,
                {"error": "Not found"},
            )
            return

        try:
            payload = self._read_json()
            if not isinstance(payload, dict):
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"error": "Request body must be a JSON object."},
                )
                return

            sender = str(payload.get("sender", "")).strip()
            message = str(payload.get("message", "")).strip()
            if not sender or not message:
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"error": "Both sender and message are required."},
                )
                return

            channel = str(payload.get("channel", "rest")).strip().lower()
            if channel == "rest":
                responses = self._send_to_rasa(
                    url=RASA_REST_URL,
                    sender=sender,
                    message=message,
                    expect_json=True,
                )
                self._send_json(HTTPStatus.OK, {"responses": responses})
                return

            if channel == "callback":
                self._send_to_rasa(
                    url=RASA_CALLBACK_URL,
                    sender=sender,
                    message=message,
                    expect_json=False,
                )
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "responses": [],
                        "callback": True,
                        "callback_endpoint": CALLBACK_ENDPOINT,
                    },
                )
                return

            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"error": "Channel must be either rest or callback."},
            )
        except ValueError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        except RuntimeError as exc:
            self._send_json(HTTPStatus.BAD_GATEWAY, {"error": str(exc)})

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format % args}")

    def _read_json(self) -> dict[str, Any] | list[Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            raise ValueError("Request body is required.")

        raw_body = self.rfile.read(content_length)
        try:
            data = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("Request body must be valid JSON.") from exc

        if not isinstance(data, (dict, list)):
            raise ValueError("Request body must be a JSON object or array.")
        return data

    def _send_to_rasa(
        self,
        url: str,
        sender: str,
        message: str,
        expect_json: bool,
    ) -> list[dict[str, Any]]:
        request_body = json.dumps({"sender": sender, "message": message}).encode("utf-8")
        request = Request(
            url,
            data=request_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=60) as response:
                response_body = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Rasa returned HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"Could not reach Rasa at {url}: {exc.reason}") from exc

        if not response_body:
            return []

        if not expect_json:
            return []

        try:
            data = json.loads(response_body)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Rasa returned non-JSON response: {response_body}") from exc

        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            return [data]
        raise RuntimeError("Rasa response must be a JSON object or array.")

    def _fetch_tracker(self, sender: str) -> dict[str, Any]:
        tracker_url = (
            f"{RASA_API_URL}/conversations/{quote(sender, safe='')}/tracker"
            "?include_events=ALL"
        )
        request = Request(tracker_url, method="GET")

        try:
            with urlopen(request, timeout=30) as response:
                response_body = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Rasa tracker returned HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"Could not reach Rasa tracker at {tracker_url}: {exc.reason}") from exc

        try:
            data = json.loads(response_body)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Rasa tracker returned non-JSON response: {response_body}") from exc

        if not isinstance(data, dict):
            raise RuntimeError("Rasa tracker response must be a JSON object.")
        return data

    def _store_callback_messages(self, messages: list[Any]) -> list[dict[str, Any]]:
        global NEXT_CALLBACK_MESSAGE_ID

        stored_messages = []
        with CALLBACK_LOCK:
            for message in messages:
                if not isinstance(message, dict):
                    continue

                NEXT_CALLBACK_MESSAGE_ID += 1
                stored_message = {"id": NEXT_CALLBACK_MESSAGE_ID, **message}
                CALLBACK_MESSAGES.append(stored_message)
                stored_messages.append(stored_message)

            del CALLBACK_MESSAGES[:-200]

        return stored_messages

    def _callback_messages(self, sender: str, after: int) -> list[dict[str, Any]]:
        with CALLBACK_LOCK:
            return [
                message
                for message in CALLBACK_MESSAGES
                if int(message.get("id", 0)) > after
                and (
                    not sender
                    or message.get("recipient_id") == sender
                    or message.get("sender") == sender
                )
            ]

    def _send_file(self, path: Path, content_type: str) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(path.read_bytes())

    def _send_json(self, status: HTTPStatus, data: dict[str, Any]) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), ChatClientHandler)
    print(f"Chat client: http://{HOST}:{PORT}")
    print(f"Rasa REST webhook: {RASA_REST_URL}")
    print(f"Rasa callback webhook: {RASA_CALLBACK_URL}")
    print(f"Configure callback.url as: {CALLBACK_ENDPOINT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
