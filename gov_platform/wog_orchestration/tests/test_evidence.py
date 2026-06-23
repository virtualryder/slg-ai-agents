from gov_platform.wog_orchestration.events import ComplianceEventBus, ComplianceEvent, assemble_evidence, retention_days

def test_retention_is_max_across_classes():
    assert retention_days(["PII", "FTI"]) == retention_days(["FTI"])  # FTI floor dominates PII
    assert retention_days(["PUBLIC"]) < retention_days(["PHI"])

def test_evidence_assembles_case_trail_with_retention():
    bus = ComplianceEventBus()
    bus.publish(ComplianceEvent("moving.form.committed", "RES-9", "SS", "form",
                                data_classes=["PII", "FTI"], correlation_id="C1", detail="x"))
    bus.publish(ComplianceEvent("moving.service_request.committed", "RES-9", "311", "service_request",
                                data_classes=["PII"], correlation_id="C1", detail="y"))
    bus.publish(ComplianceEvent("other.thing", "RES-OTHER", "X", "z", correlation_id="C9"))
    pkg = assemble_evidence(bus, "RES-9", correlation_id="C1")
    assert len(pkg.events) == 2
    assert "FTI" in pkg.data_classes
    assert pkg.binding_retention_days == retention_days(["FTI"])
    assert not pkg.was_compensated

def test_evidence_flags_compensation():
    bus = ComplianceEventBus()
    bus.publish(ComplianceEvent("moving.form.committed", "RES-9", "SS", "form", correlation_id="C1"))
    bus.publish(ComplianceEvent("moving.form.compensated", "RES-9", "SS", "form", correlation_id="C1"))
    assert assemble_evidence(bus, "RES-9", "C1").was_compensated
