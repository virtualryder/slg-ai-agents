import json, sys
from pathlib import Path
_pp = Path(__file__).resolve().parents
if len(_pp) > 3:  # local/test layout only; in AWS Lambda these come from the shared layer
    sys.path.insert(0, str(_pp[3] / "aws-native-reference/01-resident-services-311"))
import core  # noqa: E402

def ok(body): return {"statusCode": 200, "body": body}
