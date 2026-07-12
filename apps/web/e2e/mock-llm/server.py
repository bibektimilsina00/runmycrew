"""Deterministic OpenAI-compatible mock for the E2E stack.

Stdlib only — no dependencies. Two behaviors:

- Judge/evaluator prompts (anything mentioning metrics or asking for a
  JSON verdict) get a parseable verdict with a generous superset of
  metric names, `passed: true`, and feedback. Evaluator defaults any
  metric it asked for but doesn't find to that metric's min, so the
  superset keeps common templates passing without prompt-parsing.
- Everything else gets "Echo: <last user message>" so specs can assert
  the exact reply.

Force a failure verdict by including the token MOCK_FAIL in the prompt.
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer

VERDICT_KEYS = ["quality", "clarity", "correctness", "completeness", "accuracy", "relevance"]


def _reply_for(body: dict) -> str:
    messages = body.get("messages") or []
    text = " ".join(str(m.get("content", "")) for m in messages)
    last_user = next(
        (str(m.get("content", "")) for m in reversed(messages) if m.get("role") == "user"),
        "",
    )
    lowered = text.lower()
    if "metric" in lowered or '"passed"' in lowered or "json verdict" in lowered:
        passed = "MOCK_FAIL" not in text
        verdict = {k: (9 if passed else 2) for k in VERDICT_KEYS}
        verdict["passed"] = passed
        verdict["feedback"] = (
            "mock judge: looks good" if passed else "mock judge: MOCK_FAIL requested"
        )
        return json.dumps(verdict)
    return f"Echo: {last_user}"


class Handler(BaseHTTPRequestHandler):
    def _send(self, payload: dict, status: int = 200) -> None:
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):  # noqa: N802
        if self.path.startswith("/v1/models"):
            self._send({"data": [{"id": "mock-model", "object": "model"}], "object": "list"})
        elif self.path == "/healthz":
            self._send({"ok": True})
        else:
            self._send({"error": "not found"}, 404)

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._send({"error": "bad json"}, 400)
            return
        if not self.path.startswith("/v1/chat/completions"):
            self._send({"error": "not found"}, 404)
            return
        content = _reply_for(body)
        self._send(
            {
                "id": "chatcmpl-mock",
                "object": "chat.completion",
                "model": body.get("model", "mock-model"),
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": content},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            }
        )

    def log_message(self, fmt, *args):  # quiet
        pass


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 9800), Handler).serve_forever()
