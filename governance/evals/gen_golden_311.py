"""
Reproducible generator for the Agent 01 (Resident Services / 311) scored golden set.

Produces governance/evals/golden/agent01_311_scored.json: labeled NYC-311-shaped
service requests with gold labels (normalized service category, complaint_type,
agency, borough) plus one duplicate pair and one near-miss non-duplicate. Gold
labels are the ground truth the scorers assert against; the NYC 311 connector's
mapping + deterministic classifier is the prediction. Grow the set by appending
cases and re-running.

    python -m governance.evals.gen_golden_311
"""
from __future__ import annotations
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "golden" / "agent01_311_scored.json"

CASES = []


def add(uid, complaint_type, descriptor, agency, agency_name, borough, address,
        status, created, category, closed="", **extra):
    rec = {"unique_key": uid, "complaint_type": complaint_type, "descriptor": descriptor,
           "agency": agency, "agency_name": agency_name, "borough": borough,
           "incident_address": address, "status": status, "created_date": created}
    if closed:
        rec["closed_date"] = closed
    gold = {"category": category, "complaint_type": complaint_type,
            "agency": agency, "borough": borough}
    gold.update(extra)
    CASES.append({"id": uid, "record": rec, "gold": gold})


_NYPD = ("NYPD", "New York City Police Department")
_HPD = ("HPD", "Department of Housing Preservation and Development")
_DOT = ("DOT", "Department of Transportation")
_DSNY = ("DSNY", "Department of Sanitation")
_DEP = ("DEP", "Department of Environmental Protection")
_DPR = ("DPR", "Department of Parks and Recreation")
_DCA = ("DCA", "Department of Consumer and Worker Protection")

# ── varied complaint types across service categories ─────────────────────────
add("31100001", "Illegal Parking", "Blocked Hydrant", *_NYPD, "MANHATTAN",
    "350 5 Avenue", "Closed", "2024-03-15", "Parking/Vehicle", closed="2024-03-18")
add("31100002", "Noise - Residential", "Loud Music/Party", *_NYPD, "BROOKLYN",
    "45 Prospect Park West", "Open", "2024-05-01", "Noise")
add("31100003", "HEAT/HOT WATER", "Entire Building", *_HPD, "BRONX",
    "1290 Grand Concourse", "Open", "2024-01-08", "Housing")
add("31100004", "Street Condition", "Pothole", *_DOT, "QUEENS",
    "88 Northern Boulevard", "In Progress", "2024-02-20", "Street/Sidewalk")
add("31100005", "Sanitation Condition", "Dirty Conditions", *_DSNY, "BROOKLYN",
    "620 Atlantic Avenue", "Closed", "2024-04-02", "Sanitation", closed="2024-04-05")
add("31100006", "Water System", "Hydrant Running", *_DEP, "MANHATTAN",
    "410 East 74 Street", "Open", "2024-06-11", "Water/Sewer")
add("31100007", "Damaged Tree", "Broken Branch", *_DPR, "STATEN ISLAND",
    "77 Victory Boulevard", "Open", "2024-06-01", "Parks/Trees")
add("31100008", "Abandoned Vehicle", "With License Plate", *_NYPD, "QUEENS",
    "104 Roosevelt Avenue", "Open", "2024-05-19", "Parking/Vehicle")
add("31100009", "Blocked Driveway", "No Access", *_NYPD, "BROOKLYN",
    "300 Ocean Avenue", "Closed", "2024-03-30", "Parking/Vehicle", closed="2024-04-01")
add("31100010", "Noise - Commercial", "Loud Talking", *_NYPD, "MANHATTAN",
    "555 Broadway", "Open", "2024-06-22", "Noise")
add("31100011", "Missed Collection", "Recycling", *_DSNY, "BRONX",
    "2400 Webster Avenue", "Closed", "2024-02-14", "Sanitation", closed="2024-02-16")
add("31100012", "Sewer", "Catch Basin Clogged", *_DEP, "QUEENS",
    "150 Jamaica Avenue", "Open", "2024-05-06", "Water/Sewer")
add("31100013", "Street Light Condition", "Street Light Out", *_DOT, "BROOKLYN",
    "900 Flatbush Avenue", "In Progress", "2024-04-18", "Street/Sidewalk")
add("31100014", "UNSANITARY CONDITION", "Pests", *_HPD, "MANHATTAN",
    "120 West 116 Street", "Open", "2024-01-27", "Housing")
add("31100015", "PLUMBING", "Leaking Pipe", *_HPD, "BRONX",
    "740 Grand Concourse", "Open", "2024-03-03", "Housing")
add("31100016", "Consumer Complaint", "Overcharge", *_DCA, "MANHATTAN",
    "230 Canal Street", "Closed", "2024-02-09", "Consumer/Business", closed="2024-03-01")
add("31100017", "Sidewalk Condition", "Cracked", *_DOT, "QUEENS",
    "62 Queens Boulevard", "Open", "2024-06-05", "Street/Sidewalk")
add("31100018", "Derelict Vehicles", "Parked", *_NYPD, "STATEN ISLAND",
    "18 Richmond Terrace", "Open", "2024-05-25", "Parking/Vehicle")
add("31100019", "Dead/Dying Tree", "Leaning", *_DPR, "BROOKLYN",
    "500 Eastern Parkway", "Open", "2024-06-14", "Parks/Trees")
add("31100020", "Traffic Signal Condition", "Signal Not Working", *_DOT, "MANHATTAN",
    "700 8 Avenue", "In Progress", "2024-04-29", "Street/Sidewalk")

# ── duplicate pair + near-miss ───────────────────────────────────────────────
# 0021 duplicates 0002 (shared complaint_type Noise - Residential + same address)
add("31100021", "Noise - Residential", "Loud Music/Party", *_NYPD, "BROOKLYN",
    "45 Prospect Park West", "Open", "2024-05-01", "Noise",
    is_duplicate=True, dup_of="31100002")
# 0022 is a near-miss (same complaint_type, DIFFERENT address) -> NOT a duplicate
add("31100022", "Noise - Residential", "Banging/Pounding", *_NYPD, "BROOKLYN",
    "12 Ocean Parkway", "Open", "2024-05-02", "Noise",
    is_duplicate=False, dup_of="31100002")


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"cases": CASES}, indent=2), encoding="utf-8")
    print(f"wrote {len(CASES)} cases -> {OUT}")


if __name__ == "__main__":
    main()
