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
