from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from backMatterBuilder import rewrite
from backMatterBuilder.profile import load_profile_from_dict


class FakeOpenAIHandler(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802
        if self.path != "/v1/chat/completions":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        user_text = payload["messages"][1]["content"]
        body = json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "content": f"REWRITTEN::{payload['model']}::<{user_text.strip()[:20]}>"
                        }
                    }
                ]
            }
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # silence test output
        pass


@pytest.fixture
def fake_endpoint():
    server = HTTPServer(("127.0.0.1", 0), FakeOpenAIHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}/v1"
    server.shutdown()


def _profile(base_url, **extra):
    return load_profile_from_dict(
        {
            "title": "T",
            "author": "A",
            "year": 2026,
            "rewrite": {"base_url": base_url, "enabled": True, **extra},
        }
    )


def test_rewrite_success(fake_endpoint):
    p = _profile(fake_endpoint, model="llama3.2")
    out = rewrite.rewrite_section("about", "Original text here.", p)
    assert out.startswith("REWRITTEN::llama3.2::")
    assert "Original text" in out


def test_rewrite_failure_keeps_original():
    p = _profile("http://127.0.0.1:1/v1", timeout=0.5)
    original = "Keep me exactly."
    assert rewrite.rewrite_section("review_ask", original, p) == original


def test_rewrite_empty_text_no_call(fake_endpoint):
    p = _profile(fake_endpoint)
    assert rewrite.rewrite_section("about", "   ", p) == "   "


def test_rewrite_uses_configured_defaults():
    p = load_profile_from_dict({"title": "T", "author": "A", "year": 2026})
    assert p.rewrite["enabled"] is False
    assert p.rewrite["base_url"] == "http://localhost:11434/v1"
    assert "sections" in p.rewrite