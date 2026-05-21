"""Minimal FAIR-aware static server for the hackathon dataset.

It serves files from `dataset/` and reflects the dataset's *own* metadata:
  - Parses `<link rel="..." href="..." [type="..."]>` from `dataset/index.html`
    and re-emits each as an HTTP `Link:` header (FAIR Signposting, RFC 9264).
  - Content-negotiates `/` and `/index.html` against `Accept`:
      * `application/ld+json` -> `dataset/metadata.jsonld` if present
      * `application/rdf+xml` -> `dataset/metadata.xml`    if present
      * otherwise             -> `dataset/index.html`
  - Returns sensible `Content-Type` and `Content-Disposition` for data files.

The server is intentionally minimal and read-only.  All FAIR-relevant state
lives in `dataset/` so destructive commits edit data, never the server.
"""

from __future__ import annotations

import argparse
import html.parser
import logging
import mimetypes
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional
from urllib.parse import unquote

logger = logging.getLogger("fair-server")

# Resolve the dataset directory relative to this file.
DATASET_DIR: Path = (Path(__file__).resolve().parent.parent / "dataset").resolve()

# Make sure non-default media types F-UJI looks for are mapped.
for ext, mime in {
    ".jsonld":  "application/ld+json",
    ".csv":     "text/csv",
    ".ttl":     "text/turtle",
    ".xml":     "application/rdf+xml",
    ".md":      "text/markdown",
}.items():
    mimetypes.add_type(mime, ext)


class _LinkParser(html.parser.HTMLParser):
    """Extract `<link rel="..." href="..." type="..." [title=...]>` tags."""

    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag.lower() != "link":
            return
        d = {k.lower(): (v or "") for k, v in attrs}
        if "rel" in d and "href" in d:
            self.links.append(d)


def parse_signposting_links(html_path: Path) -> list[str]:
    """Return a list of fully-formed `Link:` header values."""
    if not html_path.is_file():
        return []
    try:
        text = html_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        logger.warning("Cannot read landing page %s: %s", html_path, exc)
        return []
    parser = _LinkParser()
    parser.feed(text)
    headers: list[str] = []
    for link in parser.links:
        parts = [f"<{link['href']}>", f'rel="{link["rel"]}"']
        if link.get("type"):
            parts.append(f'type="{link["type"]}"')
        if link.get("title"):
            parts.append(f'title="{link["title"]}"')
        headers.append("; ".join(parts))
    return headers


def _negotiated_target(path: str, accept: str) -> Optional[Path]:
    """Map a request path + Accept header to a file under DATASET_DIR."""
    # Strip any query.
    clean = unquote(path.split("?", 1)[0]).lstrip("/")
    # Root request: content-negotiate.
    if clean in ("", "index.html", "index"):
        if "application/ld+json" in accept:
            jsonld = DATASET_DIR / "metadata.jsonld"
            if jsonld.is_file():
                return jsonld
        if "application/rdf+xml" in accept or "text/xml" in accept:
            rdf = DATASET_DIR / "metadata.xml"
            if rdf.is_file():
                return rdf
        index = DATASET_DIR / "index.html"
        return index if index.is_file() else None
    # Direct file request — must stay inside the dataset directory.
    candidate = (DATASET_DIR / clean).resolve()
    try:
        candidate.relative_to(DATASET_DIR)
    except ValueError:
        return None
    if candidate.is_file():
        return candidate
    return None


class FairHandler(BaseHTTPRequestHandler):
    server_version = "fair-hackathon-server/1.0"

    # Cache the Signposting header list per request; cheap because index.html is small.
    def _emit_signposting(self) -> None:
        for value in parse_signposting_links(DATASET_DIR / "index.html"):
            self.send_header("Link", value)

    def _serve(self, include_body: bool) -> None:
        accept = self.headers.get("Accept", "")
        target = _negotiated_target(self.path, accept)
        if target is None:
            self.send_error(HTTPStatus.NOT_FOUND, "Resource not found")
            return
        ctype, _ = mimetypes.guess_type(str(target))
        if ctype is None:
            ctype = "application/octet-stream"
        # Charset for textual responses.
        if ctype.startswith("text/") or ctype in {"application/ld+json", "application/rdf+xml"}:
            ctype = f"{ctype}; charset=utf-8"
        try:
            size = target.stat().st_size
        except OSError as exc:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(size))
        self.send_header("Access-Control-Allow-Origin", "*")
        # Vary so caches don't confuse JSON-LD vs HTML.
        self.send_header("Vary", "Accept")
        # Friendly download name for non-HTML files.
        if target.suffix in {".csv", ".jsonld", ".xml"}:
            self.send_header("Content-Disposition", f'inline; filename="{target.name}"')
        self._emit_signposting()
        self.end_headers()
        if include_body:
            with target.open("rb") as fh:
                while chunk := fh.read(65536):
                    self.wfile.write(chunk)

    def do_GET(self) -> None:      # noqa: N802 - http.server interface
        self._serve(include_body=True)

    def do_HEAD(self) -> None:     # noqa: N802 - http.server interface
        self._serve(include_body=False)

    def log_message(self, fmt: str, *args) -> None:  # noqa: D401 - reuse parent style
        logger.info("%s - %s", self.address_string(), fmt % args)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="0.0.0.0",
                        help="Bind address (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000,
                        help="Bind port (default: 8000)")
    args = parser.parse_args()

    logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s %(message)s",
                        level=logging.INFO)
    if not DATASET_DIR.is_dir():
        logger.error("dataset directory missing: %s", DATASET_DIR)
        return 1

    httpd = ThreadingHTTPServer((args.host, args.port), FairHandler)
    logger.info("Serving %s at http://%s:%d/", DATASET_DIR, args.host, args.port)
    logger.info("From the F-UJI container, evaluate http://host.docker.internal:%d/", args.port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down.")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
