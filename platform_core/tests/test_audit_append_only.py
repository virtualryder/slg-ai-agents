"""Append-only audit enforcement: overwrites and mutations are rejected at the write path."""
import pytest

from slg_agent_platform.mcp_gateway.audit_sinks import AppendOnlyStore, AppendOnlyViolation


def test_first_write_succeeds():
    s = AppendOnlyStore()
    assert s.put({"audit_id": "a1", "decision": "ALLOW"}) == "a1"
    assert s.get("a1")["decision"] == "ALLOW" and len(s) == 1


def test_overwrite_rejected():
    s = AppendOnlyStore()
    s.put({"audit_id": "a1", "decision": "ALLOW"})
    with pytest.raises(AppendOnlyViolation):
        s.put({"audit_id": "a1", "decision": "TAMPERED"})        # cannot overwrite
    assert s.get("a1")["decision"] == "ALLOW"                    # original intact


def test_no_mutation_or_delete_api():
    s = AppendOnlyStore()
    # The store deliberately exposes no update/delete surface.
    assert not hasattr(s, "update")
    assert not hasattr(s, "delete")


def test_missing_audit_id_rejected():
    with pytest.raises(AppendOnlyViolation):
        AppendOnlyStore().put({"decision": "ALLOW"})
