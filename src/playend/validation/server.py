"""Local validation tool: serves the page, the items, the dataset images, and records the verdicts.

Everything stays on this computer (127.0.0.1): no image is uploaded anywhere.
Verdicts are appended to validation_results.jsonl (one line per click; the latest line of an item wins).

usage: python -m playend.validation.server [--port 8765] [--no-browser] [--round FOLDER]
       (opens http://127.0.0.1:8765 in the browser; Ctrl+C stops the server)
With --round, the items and the answers are those of a later round (a folder of data/validation/, see
playend.validation.corrections), kept apart from the first validation.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime
import json
import re
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playend.common.files import read_jsonl
from playend.common.paths import CAPTURES, VALIDATION

PAGE = Path(__file__).resolve().parent / "static" / "index.html"
ITEMS = VALIDATION / "items.json"
RESULTS = VALIDATION / "validation_results.jsonl"
VERDICTS = {"ok", "faux", "doute"}
LOCK = threading.Lock()
_image_index: dict[str, dict[int, Path]] = {}


def image_path(session_id: str, frame_id: int) -> Path | None:
    if session_id not in _image_index:
        folder = CAPTURES / session_id / "images"
        _image_index[session_id] = {int(p.stem.split("_")[-1]): p for p in folder.rglob("frame_*.jpg")}
    return _image_index[session_id].get(frame_id)


def latest_results() -> dict:
    """The last answer given for each item (the file keeps every click)."""
    return {row["item_id"]: row for row in read_jsonl(Handler.results)} if Handler.results.exists() else {}


class Handler(BaseHTTPRequestHandler):
    items, results = ITEMS, RESULTS

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store" if ctype.startswith("application/json") else "max-age=3600")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            return self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
        if self.path == "/items":
            return self._send(200, self.items.read_bytes())
        if self.path == "/results":
            return self._send(200, json.dumps(latest_results(), ensure_ascii=False))
        match = re.fullmatch(r"/img/(session_[0-9a-f]{32})/(\d+)", self.path)
        if match:
            path = image_path(match.group(1), int(match.group(2)))
            if path and path.is_file():
                return self._send(200, path.read_bytes(), "image/jpeg")
        return self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        if self.path != "/save":
            return self._send(404, json.dumps({"error": "not found"}))
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(min(length, 100_000)).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return self._send(400, json.dumps({"error": "invalid json"}))
        item_id, verdict = payload.get("item_id"), payload.get("verdict")
        if not isinstance(item_id, str) or verdict not in VERDICTS:
            return self._send(400, json.dumps({"error": "item_id and verdict (ok|faux|doute) required"}))
        row = {
            "item_id": item_id,
            "verdict": verdict,
            "champs_faux": [str(x) for x in payload.get("champs_faux", [])][:20],
            "commentaire": str(payload.get("commentaire", ""))[:2000],
            "relecteur": "utilisateur",
            "horodatage_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        }
        with LOCK, self.results.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
        return self._send(200, json.dumps({"saved": True}))

    def log_message(self, *args):
        pass


def main():
    parser = argparse.ArgumentParser(description="Local validation tool: serves the page and records the answers.")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true", help="do not open the page in the browser")
    parser.add_argument("--round", help="folder of data/validation/ with a later round of items (corrections)")
    args = parser.parse_args()
    if args.round:
        Handler.items, Handler.results = (
            VALIDATION / args.round / "items.json",
            VALIDATION / args.round / "results.jsonl",
        )
    url = f"http://127.0.0.1:{args.port}"
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Outil de validation : {url}  (Ctrl+C pour arrêter)")
    if not args.no_browser:
        threading.Timer(1.0, webbrowser.open, [url]).start()
    with contextlib.suppress(KeyboardInterrupt):
        server.serve_forever()


if __name__ == "__main__":
    main()
