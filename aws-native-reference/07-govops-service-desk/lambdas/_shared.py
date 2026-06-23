import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "aws-native-reference/07-govops-service-desk"))
import core  # noqa: E402
def ok(b): return {"statusCode":200,"body":b}
