import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import core
def test_classify_and_actions():
    for intent in core.INTENT_KEYWORDS:
        assert core.recommended_action(intent)
    a=core.recommended_action(core.DEFAULT_INTENT)
    assert isinstance(core.is_write_action(a), bool)
