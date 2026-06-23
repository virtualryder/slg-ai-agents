"""
Structural eval harness. Validates that key artifacts keep their required shape —
the anatomy a reviewer and an auditor depend on. No API key, no network.
"""
from __future__ import annotations

import sys
from typing import Callable, Dict, List, Tuple

from .golden_artifacts import RESIDENT_ANSWER, FOIA_PACKAGE


def _resident_answer_ok(a: Dict) -> Tuple[bool, str]:
    if not a.get("answer"):
        return False, "missing answer"
    if not a.get("citations"):
        return False, "resident answer must carry citations"
    for c in a["citations"]:
        if not c.get("url"):
            return False, "every citation needs a URL"
    return True, "ok"


def _foia_package_ok(p: Dict) -> Tuple[bool, str]:
    if not p.get("index"):
        return False, "FOIA package needs an index"
    if "proposed_redactions" not in p:
        return False, "FOIA package must propose redactions for human review"
    if p.get("released") is not False:
        return False, "agent artifact must not be auto-released (human gate)"
    return True, "ok"


CASES: List[Tuple[str, Callable, Dict]] = [
    ("resident_answer_anatomy", _resident_answer_ok, RESIDENT_ANSWER),
    ("foia_package_anatomy", _foia_package_ok, FOIA_PACKAGE),
]


def run() -> int:
    failures = 0
    for name, fn, art in CASES:
        ok, msg = fn(art)
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {msg}")
        failures += 0 if ok else 1
    print(f"\n{len(CASES) - failures}/{len(CASES)} eval cases passed")
    return failures


if __name__ == "__main__":
    sys.exit(0 if run() == 0 else 1)
