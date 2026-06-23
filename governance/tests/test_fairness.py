from governance.fairness.disparate_impact import four_fifths

def test_four_fifths_flags_disparity():
    rep = four_fifths(selected={"A": 50, "B": 10}, totals={"A": 100, "B": 100})
    assert not rep.passes_four_fifths and "B" in rep.flagged_groups

def test_four_fifths_passes_when_balanced():
    rep = four_fifths(selected={"A": 40, "B": 38}, totals={"A": 100, "B": 100})
    assert rep.passes_four_fifths
