"""
PII / CJI / FTI masking — SLG data-protection support at the log/audit boundary.

Logs, traces, and audit records in a state & local government workload must never
contain raw protected identifiers. This module gives every agent one masking
function applied at log/audit boundaries. It targets the identifier families most
likely to appear in 311 text, benefit applications, permit packets, records
requests, and incident narratives — the data classes called out by the SLG
compliance matrix:

    * US SSN                         123-45-6789        (IRS Pub 1075 / FTI, PII)
    * Driver's license / state ID    DL/OLN patterns    (DPPA — 18 U.S.C. 2721)
    * Case / application / permit IDs CASE-/APP-/PRM- prefixes + long digit runs
    * Dates more specific than year  (DOB, incident dates)
    * Email addresses, phone/fax numbers
    * Payment card numbers (Luhn-validated, for fee / utility-payment flows; PCI)
    * Street addresses (number + street-type) — DPPA / privacy
    * FEIN / EIN (XX-XXXXXXX) for business registration & procurement

Design notes:
  * Deterministic and dependency-free (regex + Luhn). An optional ML NER pass
    (Amazon Comprehend / Presidio) can be layered behind MASK_ENGINE=ml.
  * Conservative: over-masking a log line is acceptable; leaking an SSN, a DL
    number, or CJI is not.
  * mask() is idempotent and safe to call on already-masked text.

This is the de-identification *control point*; it does NOT replace a formal data-
set de-identification or the agency's records-retention and CJIS/FTI handling
program, which are governed by the customer's privacy and security officers.
"""
from __future__ import annotations

import os
import re
from typing import Optional

# ── Identifier patterns (order matters: most specific first) ──────────────────
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_EIN_RE = re.compile(r"\b\d{2}-\d{7}\b")  # FEIN / EIN (business, procurement)
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE_RE = re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
# Driver's license / state ID with common labels, and case / app / permit IDs
_DL_RE = re.compile(r"\b(?:DL|OLN|DLN|LIC|LICENSE)[-#:\s]?[A-Z0-9]{5,}\b", re.I)
_CASEID_RE = re.compile(
    r"\b(?:CASE|APP|APPL|PERMIT|PRM|REC|FOIA|SR|TICKET|INC|GRANT|RFP|BID)[-_ ]?\d{3,}\b", re.I
)
# Dates more specific than a bare year (YYYY-MM-DD, MM/DD/YYYY, DD-Mon-YYYY)
_DATE_RE = re.compile(
    r"\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}|"
    r"\d{1,2}[-\s](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[-\s]\d{2,4})\b",
    re.I,
)
# Street address: number + name + street-type suffix
_ADDRESS_RE = re.compile(
    r"\b\d{1,6}\s+(?:[A-Za-z0-9.'-]+\s+){0,4}"
    r"(?:St|Street|Ave|Avenue|Blvd|Boulevard|Rd|Road|Ln|Lane|Dr|Drive|Ct|Court|"
    r"Way|Pl|Place|Ter|Terrace|Cir|Circle|Hwy|Highway|Pkwy|Parkway)\b\.?",
    re.I,
)
# 13-19 digit runs that pass Luhn -> payment cards (fee / utility payments)
_CARD_RE = re.compile(r"\b(?:\d[ -]?){13,19}\b")
# Long bare digit runs (>=9) -> account / case / parcel-style identifiers
_LONGNUM_RE = re.compile(r"\b\d{9,}\b")


def luhn_valid(number: str) -> bool:
    """Return True if the digit string passes the Luhn checksum."""
    digits = [int(c) for c in number if c.isdigit()]
    if len(digits) < 13:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def _mask_cards(text: str) -> str:
    def repl(m: re.Match) -> str:
        raw = m.group(0)
        return "[CARD-REDACTED]" if luhn_valid(raw) else raw
    return _CARD_RE.sub(repl, text)


def mask(text: Optional[str]) -> str:
    """
    Mask PII/CJI/FTI identifiers in free text for safe logging and audit.

    Idempotent; returns "" for None. Set MASK_ENGINE=ml to additionally run an
    optional NER engine (not bundled — wired by the customer's privacy stack).
    """
    if not text:
        return ""
    out = str(text)
    out = _SSN_RE.sub("[SSN-REDACTED]", out)
    out = _EIN_RE.sub("[EIN-REDACTED]", out)
    out = _EMAIL_RE.sub("[EMAIL-REDACTED]", out)
    out = _DL_RE.sub("[DL-REDACTED]", out)
    out = _CASEID_RE.sub("[CASE-ID-REDACTED]", out)
    out = _mask_cards(out)
    out = _PHONE_RE.sub("[PHONE-REDACTED]", out)
    out = _ADDRESS_RE.sub("[ADDRESS-REDACTED]", out)
    out = _DATE_RE.sub("[DATE-REDACTED]", out)
    out = _LONGNUM_RE.sub("[ID-REDACTED]", out)

    if os.getenv("MASK_ENGINE", "").strip().lower() == "ml":
        out = _ml_mask(out)
    return out


def _ml_mask(text: str) -> str:
    """Optional ML NER hook (Amazon Comprehend / Presidio). No-op if absent."""
    try:  # pragma: no cover - optional dependency path
        from slg_agent_platform._ml_ner import redact  # type: ignore

        return redact(text)
    except Exception:
        return text
