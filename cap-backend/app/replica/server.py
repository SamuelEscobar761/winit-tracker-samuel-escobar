import copy
import json
import random
import threading
import time
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.cases.parsing.search_parser import parse_search_response
from app.providers.mock.catalog import MockCatalog, load_mock_catalog
from app.providers.mock.portal_query import canonical_portal_query
from app.providers.mock.synthetic_detail import build_synthetic_detail_payload
from app.replica.page import PAGE_TEMPLATE

SESSION_COOKIE = "replica_session"
EXPIRED_MESSAGE = "Traffic Payment Session Expired."


@dataclass
class ReplicaState:
    valid_tokens: set[str] = field(default_factory=set)
    token_counter: int = 0
    session_expired: bool = False
    maintenance: bool = False
    application_mode: str = "NORMAL"
    empty_result_as_error: bool = True
    show_captcha: bool = False
    search_delay_seconds: float = 0.0
    party_label: str = "Party Name"
    search_path: str = "/api/traffic/search"
    case_number_key: str = "caseNumber"
    failure_rate: float = 0.0
    captcha_rate: float = 0.0
    generator: random.Random = field(default_factory=random.Random)
    pending_captcha: set[str] = field(default_factory=set)
    calls: list[str] = field(default_factory=list)

    def issue_token(self) -> str:
        self.token_counter += 1
        token = f"token-{self.token_counter}"
        self.valid_tokens.add(token)
        return token

    def is_valid(self, token: str | None) -> bool:
        return not self.session_expired and token in self.valid_tokens

    def should_fail(self) -> bool:
        return self.failure_rate > 0 and self.generator.random() < self.failure_rate

    def should_show_new_captcha(self) -> bool:
        return self.captcha_rate > 0 and self.generator.random() < self.captcha_rate


class ReplicaPortal:
    """A local page with the look, flow, ids and API of the real `/traffic` portal."""

    def __init__(self, fixtures_dir: Path, state: ReplicaState | None = None) -> None:
        self.state = state or ReplicaState()
        self._catalog = load_mock_catalog(fixtures_dir)
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), self._build_handler())
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self._server.server_address[1]}/traffic"

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()

    def _build_handler(self) -> type[BaseHTTPRequestHandler]:
        state, catalog = self.state, self._catalog

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:
                return None

            def do_GET(self) -> None:
                _route_get(self, state, catalog)

            def do_POST(self) -> None:
                _route_post(self, state, catalog)

        return Handler


def _send_json(handler: BaseHTTPRequestHandler, body: Any, status: int = 200) -> None:
    data = json.dumps(body).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def _envelope(data: Any, result: int = 0, message: str = "") -> dict[str, Any]:
    return {"data": data, "result": result, "created": "2026-10-16T00:00:00Z", "message": message}


def _session_id(handler: BaseHTTPRequestHandler) -> str | None:
    for part in handler.headers.get("Cookie", "").split(";"):
        name, _, value = part.strip().partition("=")
        if name == SESSION_COOKIE:
            return value
    return None


def _route_get(handler: BaseHTTPRequestHandler, state: ReplicaState, catalog: MockCatalog) -> None:
    path = handler.path
    state.calls.append(f"GET {path}")
    if path.startswith("/traffic"):
        _send_page(handler, state)
    elif path == "/api/traffic/token":
        _send_json(handler, {"token": state.issue_token()})
    elif path == "/api/maintenance":
        _send_json(handler, _envelope(state.maintenance))
    elif path == "/api/applicationmode":
        _send_json(handler, state.application_mode)
    elif path.startswith("/api/traffic/select/"):
        _select(handler, state, catalog, path.rsplit("/", 1)[1])
    else:
        _send_json(handler, {}, 404)


def _send_page(handler: BaseHTTPRequestHandler, state: ReplicaState) -> None:
    page = (
        PAGE_TEMPLATE.replace("{{PARTY_LABEL}}", state.party_label)
        .replace("{{SEARCH_PATH}}", state.search_path)
        .replace("{{CASE_KEY}}", state.case_number_key)
    )
    data = page.encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    if _session_id(handler) is None:
        handler.send_header("Set-Cookie", f"{SESSION_COOKIE}={uuid4().hex}; Path=/")
    handler.end_headers()
    handler.wfile.write(data)


def _route_post(handler: BaseHTTPRequestHandler, state: ReplicaState, catalog: MockCatalog) -> None:
    state.calls.append(f"POST {handler.path}")
    length = int(handler.headers.get("Content-Length", "0"))
    body = json.loads(handler.rfile.read(length) or b"{}")
    if handler.path == state.search_path:
        _search(handler, state, catalog, body)
    elif handler.path == "/api/replica/captcha-solved":
        state.pending_captcha.discard(_session_id(handler) or "")
        _send_json(handler, _envelope(True))
    else:
        _send_json(handler, {}, 404)


def _injected_failure(handler: BaseHTTPRequestHandler, state: ReplicaState) -> bool:
    if not state.should_fail():
        return False
    if state.generator.random() < 0.5:
        _send_json(handler, _envelope({}, 1, EXPIRED_MESSAGE))
    else:
        _send_json(handler, {}, 503)
    return True


def _search(
    handler: BaseHTTPRequestHandler,
    state: ReplicaState,
    catalog: MockCatalog,
    body: dict[str, Any],
) -> None:
    time.sleep(state.search_delay_seconds)
    if not state.is_valid(handler.headers.get("portal-token")):
        _send_json(handler, _envelope({}, 1, EXPIRED_MESSAGE))
        return
    if _injected_failure(handler, state):
        return
    payload = catalog.search_payload(canonical_portal_query(str(body.get("value", ""))))
    if payload is None:
        _send_json(handler, _empty_result(state))
        return
    answer = copy.deepcopy(payload)
    answer["captcha"] = _needs_captcha(handler, state)
    _rename_case_number(answer, state.case_number_key)
    _send_json(handler, answer)


def _needs_captcha(handler: BaseHTTPRequestHandler, state: ReplicaState) -> bool:
    session = _session_id(handler) or ""
    if state.should_show_new_captcha():
        state.pending_captcha.add(session)
    return state.show_captcha or session in state.pending_captcha


def _empty_result(state: ReplicaState) -> dict[str, Any]:
    if state.empty_result_as_error:
        return _envelope(None, 1, "No Case(s) Found")
    return _envelope([], 0, "No Case(s) Found")


def _select(
    handler: BaseHTTPRequestHandler, state: ReplicaState, catalog: MockCatalog, case_number: str
) -> None:
    if not state.is_valid(handler.headers.get("portal-token")):
        _send_json(handler, _envelope({}, 1, EXPIRED_MESSAGE))
        return
    if _injected_failure(handler, state):
        return
    key = case_number.replace("-", "").upper()
    recorded = catalog.detail_payload(key)
    _send_json(handler, recorded or _synthetic_detail(catalog, case_number))


def _synthetic_detail(catalog: MockCatalog, case_number: str) -> dict[str, Any]:
    for payload in catalog.search_payloads.values():
        for case in parse_search_response(payload):
            if case.case_number == case_number:
                return build_synthetic_detail_payload(case, catalog)
    return _envelope({}, 1, "Case not found")


def _rename_case_number(answer: dict[str, Any], new_key: str) -> None:
    if new_key == "caseNumber" or not isinstance(answer.get("data"), list):
        return
    for item in answer["data"]:
        item[new_key] = item.pop("caseNumber")
