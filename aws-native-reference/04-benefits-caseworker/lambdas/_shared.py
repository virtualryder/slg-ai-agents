import sys
from pathlib import Path
_pp = Path(__file__).resolve().parents
if len(_pp) > 3:  # local/test layout only; in AWS Lambda these come from the shared layer
    sys.path.insert(0, str(_pp[3] / "aws-native-reference/04-benefits-caseworker"))
import core  # noqa: E402
def ok(b): return {"statusCode":200,"body":b}
