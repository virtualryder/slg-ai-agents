from governance.prompt_registry import verify, load_manifest

def test_manifest_loads():
    assert "01-resident-services.answer" in load_manifest()

def test_registered_prompt_matches_pin():
    text = (
        "You are a city resident-services assistant. Answer ONLY from the provided "
        "approved knowledge sources. Cite the source title and URL for every fact. "
        "If the answer requires personal account data, require identity verification "
        "first. Never disclose application, tax, benefit, or case details based only "
        "on a name and address. If unsure, route to a human."
    )
    assert verify("01-resident-services.answer", text)

def test_drift_detected():
    assert not verify("01-resident-services.answer", "tampered prompt")
