#!/usr/bin/env python3
"""
Lab 14 — verify Argo Rollouts dashboard HTTP surface while
`kubectl argo rollouts dashboard` is running (stdlib only).

Usage:
  python3 k8s/rollout_dashboard_check.py
  python3 k8s/rollout_dashboard_check.py --base http://127.0.0.1:8080
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request


def get(url: str, timeout: float = 10.0) -> tuple[int, dict[str, str], bytes]:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            headers = {k: v for k, v in resp.headers.items()}
            return resp.status, headers, resp.read()
    except urllib.error.HTTPError as e:
        body = e.read() if e.fp else b""
        return e.code, {k: v for k, v in e.headers.items()}, body


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--base",
        default="http://127.0.0.1:3100",
        help="Dashboard base URL (same host/port as kubectl argo rollouts dashboard)",
    )
    args = p.parse_args()
    base = args.base.rstrip("/")

    ok = True
    print(f"Base: {base}\n")

    # Root may redirect to /rollouts/ or serve the SPA (depends on plugin version).
    code, h, body = get(base + "/")
    if code in (301, 302, 303, 307, 308):
        print(f"[OK] GET / -> {code} Location: {h.get('Location', '')}")
    elif code == 200 and b"rollouts" in body[:500].lower():
        print(f"[OK] GET / -> {code} (HTML shell)")
    else:
        print(f"[FAIL] GET / -> {code}")
        ok = False

    code, _, body = get(base + "/rollouts/")
    print(f"[{'OK' if code == 200 else 'FAIL'}] GET /rollouts/ -> {code}")
    if code != 200:
        ok = False
    html = body.decode("utf-8", errors="replace")
    m = re.search(r'src="(main\.[a-f0-9]+\.js)"', html)
    if not m:
        print("     FAIL: could not find main.*.js in HTML")
        ok = False
    else:
        js_name = m.group(1)
        c, _, _ = get(base + "/rollouts/" + js_name)
        print(f"[{'OK' if c == 200 else 'FAIL'}] GET /rollouts/{js_name} -> {c}")
        if c != 200:
            ok = False

    c, _, _ = get(base + "/rollouts/main.css")
    print(f"[{'OK' if c == 200 else 'FAIL'}] GET /rollouts/main.css -> {c}")
    if c != 200:
        ok = False

    # REST API is under /api (not under /rollouts — base href must not apply)
    c, h, body = get(base + "/api/v1/version")
    ct = h.get("Content-Type", "")
    print(f"[{'OK' if c == 200 and 'json' in ct else 'FAIL'}] GET /api/v1/version -> {c} ({ct})")
    if c != 200:
        ok = False
    try:
        ver = json.loads(body.decode())
        print(f"     version payload keys: {list(ver.keys())[:8]}")
    except json.JSONDecodeError:
        print("     FAIL: not JSON")
        ok = False

    c, _, body = get(base + "/api/v1/namespace")
    print(f"[{'OK' if c == 200 else 'FAIL'}] GET /api/v1/namespace -> {c}")
    if c != 200:
        ok = False
    ns = "default"
    try:
        data = json.loads(body.decode())
        avail = data.get("availableNamespaces") or []
        if avail:
            ns = avail[0]
        print(f"     using namespace for info: {ns}")
    except json.JSONDecodeError:
        print("     FAIL: namespace response not JSON")
        ok = False

    c, _, body = get(base + f"/api/v1/rollouts/{ns}/info")
    print(f"[{'OK' if c == 200 else 'FAIL'}] GET /api/v1/rollouts/{ns}/info -> {c}")
    if c != 200:
        ok = False
    try:
        info = json.loads(body.decode())
        n = len(info.get("rollouts") or [])
        print(f"     rollouts in {ns}: {n}")
    except json.JSONDecodeError:
        print("     FAIL: info response not JSON")
        ok = False

    print()
    if ok:
        print("SUMMARY: HTTP checks passed. If the browser still spins, use Chrome or Edge;")
        print("the UI loads data via gRPC-Web, which Safari often does not support.")
        return 0
    print("SUMMARY: one or more checks failed. Fix HTTP errors before debugging the browser.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
