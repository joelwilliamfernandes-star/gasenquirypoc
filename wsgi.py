#!/usr/bin/env python3
"""WSGI entry point for deploying Gas Enquiry on PythonAnywhere."""

from html import escape
import os
from pathlib import Path
import sys
from urllib.parse import parse_qs

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app as gas_app
from page_framework import render_information_page


def _html_shell(document: str) -> str:
    """Apply the shared site chrome and stylesheet to an HTML document."""
    document = document.replace(
        "</head>", '<link rel="stylesheet" href="/static/styles.css"></head>', 1
    )
    shell = '''<a class="skip-link" href="#main-content">Skip to main content</a>
<header class="site-header"><div class="site-header-inner">
<a class="site-brand" href="/"><strong>Gas Enquiry</strong><span>Supply point information</span></a>
<nav class="site-nav" aria-label="Main navigation"><a href="/" aria-current="page">MPRN Search</a></nav>
</div><div class="header-accent" aria-hidden="true"></div></header><main class="app-main" id="main-content">'''
    document = document.replace("<body>", "<body>" + shell, 1)
    return document.replace("</body>", "</main></body>", 1)


def _response(start_response, status: int, body: str | bytes,
              content_type: str = "text/html; charset=utf-8", headers=()):
    if isinstance(body, str) and content_type.startswith("text/html"):
        body = _html_shell(body)
    payload = body.encode("utf-8") if isinstance(body, str) else body
    phrases = {
        200: "200 OK", 303: "303 See Other", 400: "400 Bad Request",
        404: "404 Not Found", 405: "405 Method Not Allowed",
        500: "500 Internal Server Error", 503: "503 Service Unavailable",
    }
    response_headers = [
        ("Content-Type", content_type),
        ("Content-Length", str(len(payload))),
        ("X-Content-Type-Options", "nosniff"),
        ("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'"),
    ]
    response_headers.extend(headers)
    start_response(phrases.get(status, f"{status} Response"), response_headers)
    return [payload]


def application(environ, start_response):
    """Serve the search and meter information routes as a WSGI application."""
    method = environ.get("REQUEST_METHOD", "GET").upper()
    path = environ.get("PATH_INFO", "/")

    if path == "/static/styles.css" and method == "GET":
        try:
            css = (ROOT / "static" / "styles.css").read_bytes()
        except OSError:
            return _response(start_response, 404, b"Not found", "text/plain; charset=utf-8")
        return _response(start_response, 200, css, "text/css; charset=utf-8")

    if path == "/" and method == "GET":
        status, document = gas_app.search_page()
        return _response(start_response, status, document)

    if path == "/search":
        if method != "POST":
            return _response(start_response, 405, "<h1>Method not allowed</h1>",
                             headers=[("Allow", "POST")])
        try:
            length = min(max(int(environ.get("CONTENT_LENGTH") or 0), 0), 4096)
            raw = environ["wsgi.input"].read(length).decode("utf-8")
            form = parse_qs(raw, keep_blank_values=True)
            mprn = form.get("mprn", [""])[0].strip()
        except (ValueError, UnicodeDecodeError, KeyError):
            status, document = gas_app.search_page("Enter a valid MPRN.", status=400)
            return _response(start_response, status, document)
        if not mprn or not mprn.isascii() or not mprn.isdigit():
            status, document = gas_app.search_page(
                "Enter a complete MPRN using digits only.", mprn, 400
            )
            return _response(start_response, status, document)
        try:
            match = gas_app.find_mprn(mprn)
        except gas_app.DatabaseError:
            status, document = gas_app.search_page(
                "The search service is temporarily unavailable. Please try again.", mprn, 503
            )
            return _response(start_response, status, document)
        if match is None:
            status, document = gas_app.search_page(
                "That MPRN was not found. Check the number and try again.", mprn, 404
            )
            return _response(start_response, status, document)
        return _response(start_response, 303, b"", headers=[("Location", f"/meter/{match}")])

    if path.startswith("/meter/") and method == "GET":
        mprn = path.removeprefix("/meter/")
        try:
            sections = gas_app.load_meter_sections(mprn)
        except gas_app.DatabaseError:
            status, document = gas_app.search_page(
                "The search service is temporarily unavailable. Please try again.", status=503
            )
            return _response(start_response, status, document)
        if sections is None:
            status, document = gas_app.search_page(
                "That MPRN was not found. Check the number and try again.", status=404
            )
            return _response(start_response, status, document)
        return _response(start_response, 200, render_information_page(mprn, sections))

    if method not in {"GET", "HEAD"}:
        return _response(start_response, 405, "<h1>Method not allowed</h1>",
                         headers=[("Allow", "GET, HEAD, POST")])
    return _response(start_response, 404,
                     '<h1>Page not found</h1><p><a href="/">Return to MPRN search</a></p>')


# PythonAnywhere looks for a WSGI callable named `application` in its config.
