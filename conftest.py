import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent
for p in (_ROOT / "platform_core", _ROOT, _ROOT / "01-resident-services-311",
          _ROOT / "aws-native-reference/01-resident-services-311"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)
