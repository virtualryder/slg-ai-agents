import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "aws-native-reference/04-benefits-caseworker"))
import core  # noqa: E402
def ok(b): return {"statusCode":200,"body":b}
