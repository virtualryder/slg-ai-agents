#!/usr/bin/env python3
"""Portfolio drift-checker for MATURITY.yaml.

Keeps ``tests.offline_total`` in MATURITY.yaml honest by re-deriving the
collected-test count from the *documented* reproduce paths and comparing.

- Repo root is resolved as the parent of this ``tools/`` directory (no CWD
  assumptions), so the script works from anywhere.
- The pytest target paths are parsed out of ``tests.reproduce`` in
  MATURITY.yaml (the parenthesized, comma-separated path list), so the check
  always mirrors whatever the file documents as the reproduce command. Glob
  patterns (e.g. ``[0-9][0-9]-*/tests``) are expanded against the repo root.
- Runs ``<python> -m pytest --collect-only -q <paths>`` via ``sys.executable``
  and counts the collected node ids.
- Exits 0 when declared == actual; exits 1 with a clear drift message otherwise.
- ``--update`` rewrites ``offline_total`` in place to the freshly counted value.

Standard library only.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from glob import glob
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MATURITY = REPO_ROOT / "MATURITY.yaml"

# offline_total: <int>  (optionally followed by a # comment)
_OFFLINE_RE = re.compile(r"^(?P<prefix>\s*offline_total:\s*)(?P<value>\d+)", re.MULTILINE)
# tests.reproduce: "...."   — captures the quoted reproduce string
_REPRODUCE_RE = re.compile(r"^\s*reproduce:\s*[\"'](?P<body>.*?)[\"']\s*$", re.MULTILINE)
# per-file collect line, e.g. "platform_core/tests/test_pii.py: 8"
_COUNT_RE = re.compile(r":\s*(\d+)\s*$")


def read_declared(text: str) -> int:
    m = _OFFLINE_RE.search(text)
    if not m:
        sys.exit("ERROR: could not find `offline_total:` in MATURITY.yaml")
    return int(m.group("value"))


def parse_reproduce_paths(text: str) -> list[str]:
    """Extract pytest target path tokens from tests.reproduce.

    The reproduce string looks like:
        run per-suite pytest (platform_core/tests, governance/tests,
        [0-9][0-9]-*/tests); see SUITE-STATUS.md
    We take the first parenthesized group and split it on commas, keeping
    only tokens that look like filesystem paths (contain a ``/``).
    """
    m = _REPRODUCE_RE.search(text)
    if not m:
        sys.exit("ERROR: could not find `reproduce:` in MATURITY.yaml")
    body = m.group("body")
    paren = re.search(r"\(([^)]*)\)", body)
    inner = paren.group(1) if paren else body
    tokens = [t.strip() for t in inner.split(",")]
    paths = [t for t in tokens if "/" in t]
    if not paths:
        sys.exit(f"ERROR: no path-like tokens parsed from reproduce string: {body!r}")
    return paths


def expand_paths(patterns: list[str]) -> list[str]:
    expanded: list[str] = []
    for pat in patterns:
        matches = sorted(glob(pat, root_dir=str(REPO_ROOT)))
        if matches:
            expanded.extend(matches)
        elif (REPO_ROOT / pat).exists():
            expanded.append(pat)
        # else: silently drop a pattern that matches nothing on disk
    return expanded


def count_collected(paths: list[str]) -> int:
    env = dict(os.environ)
    pc = str(REPO_ROOT / "platform_core")
    env["PYTHONPATH"] = os.pathsep.join([pc, str(REPO_ROOT), env.get("PYTHONPATH", "")]).rstrip(os.pathsep)
    cmd = [sys.executable, "-m", "pytest", "--collect-only", "-q", *paths]
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), env=env, capture_output=True, text=True)
    out = proc.stdout + proc.stderr
    if proc.returncode != 0 and "collected" not in out and not _COUNT_RE.search(out):
        sys.stderr.write(out)
        sys.exit(f"ERROR: pytest collection failed (exit {proc.returncode})")

    # Primary: node-id lines ("path::test_name[...]").
    node_ids = [ln for ln in out.splitlines() if "::" in ln]
    if node_ids:
        return len(node_ids)
    # Fallback: modern quiet collect prints "path: N" per file — sum them.
    total = 0
    found = False
    for ln in out.splitlines():
        m = _COUNT_RE.search(ln)
        if m and ("/" in ln or ln.strip().endswith(m.group(0).strip())):
            total += int(m.group(1))
            found = True
    if not found:
        sys.stderr.write(out)
        sys.exit("ERROR: could not parse a collected-test count from pytest output")
    return total


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--update", action="store_true",
                    help="rewrite offline_total in MATURITY.yaml to the freshly counted value")
    args = ap.parse_args()

    text = MATURITY.read_text()
    declared = read_declared(text)
    patterns = parse_reproduce_paths(text)
    paths = expand_paths(patterns)
    print(f"reproduce paths: {', '.join(patterns)}")
    print(f"expanded to {len(paths)} target(s)")
    actual = count_collected(paths)

    print(f"declared offline_total : {declared}")
    print(f"actual collected count : {actual}")

    if args.update:
        if declared == actual:
            print("no update needed (already in sync)")
            return 0
        new_text = _OFFLINE_RE.sub(lambda m: f"{m.group('prefix')}{actual}", text, count=1)
        MATURITY.write_text(new_text)
        print(f"updated offline_total: {declared} -> {actual}")
        return 0

    if declared != actual:
        print(f"DRIFT: MATURITY.yaml declares offline_total={declared} but the documented "
              f"suite collects {actual}. Run `python tools/check_maturity.py --update` to fix.")
        return 1
    print("OK: offline_total matches collected count.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
