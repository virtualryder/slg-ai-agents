"""Tests for the PII/CJI/FTI masker."""
from slg_agent_platform.pii import mask, luhn_valid


def test_masks_ssn_and_is_idempotent():
    once = mask("SSN 123-45-6789 on file")
    assert "123-45-6789" not in once and "[SSN-REDACTED]" in once
    assert mask(once) == once


def test_masks_drivers_license_and_email_and_phone():
    out = mask("DL D1234567, email a@b.gov, call (555) 123-4567")
    assert "[DL-REDACTED]" in out and "[EMAIL-REDACTED]" in out and "[PHONE-REDACTED]" in out


def test_masks_case_ids_and_address():
    out = mask("Permit PRM-2026-0481 at 123 Main Street")
    assert "[CASE-ID-REDACTED]" in out and "[ADDRESS-REDACTED]" in out


def test_masks_valid_card_only():
    assert "[CARD-REDACTED]" in mask("card 4111111111111111")
    assert "4242" in mask("order 4242 widgets")  # short number untouched


def test_none_returns_empty():
    assert mask(None) == ""


def test_luhn():
    assert luhn_valid("4111111111111111")
    assert not luhn_valid("4111111111111112")


def test_ml_masking_fails_closed_by_default(monkeypatch):
    # MASK_ENGINE=ml but the ML NER module is absent -> must NOT return raw text.
    monkeypatch.setenv("MASK_ENGINE", "ml")
    monkeypatch.delenv("MASK_FAIL_CLOSED", raising=False)
    from slg_agent_platform import pii
    out = pii.mask("contact Jane at 123 Main St about SSN 123-45-6789")
    assert out == pii._FAILCLOSED_PLACEHOLDER
    assert "123-45-6789" not in out and "Main St" not in out


def test_ml_masking_fail_open_is_opt_in(monkeypatch):
    # Explicit opt-in (MASK_FAIL_CLOSED=0) keeps the regex-masked text on ML failure.
    monkeypatch.setenv("MASK_ENGINE", "ml")
    monkeypatch.setenv("MASK_FAIL_CLOSED", "0")
    from slg_agent_platform import pii
    out = pii.mask("SSN 123-45-6789")
    assert "123-45-6789" not in out          # regex masking still applied
    assert out != pii._FAILCLOSED_PLACEHOLDER
