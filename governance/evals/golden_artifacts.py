"""Known-good reference artifacts a prompt/model change must not regress (structure)."""

RESIDENT_ANSWER = {
    "answer": "Residential trash is collected weekly on your zone day; recycling is biweekly.",
    "citations": [{"title": "Residential Trash & Recycling Schedule",
                   "url": "https://city.example.gov/trash"}],
    "identity_required": False,
    "routed_to_human": False,
}

FOIA_PACKAGE = {
    "package_id": "PKG-3120",
    "index": [{"record_id": "REC-9002", "type": "Email", "responsive": True}],
    "proposed_redactions": [{"type": "SSN", "page": 1}],
    "ready_for_review": True,
    "released": False,  # release is a human records-officer action
}
