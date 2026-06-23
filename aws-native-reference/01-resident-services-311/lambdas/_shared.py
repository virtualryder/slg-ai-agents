import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "aws-native-reference/01-resident-services-311"))
import core  # noqa: E402

def ok(body): return {"statusCode": 200, "body": body}
