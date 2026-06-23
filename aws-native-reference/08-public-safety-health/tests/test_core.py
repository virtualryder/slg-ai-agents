import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import core

def test_classify_default():
    assert core.classify("summarize") in core.INTENT_KEYWORDS or core.classify("zzz") == core.DEFAULT_INTENT

def test_write_action_flag():
    a = core.recommended_action(core.DEFAULT_INTENT)
    assert core.is_write_action(a) or a == "ESCALATE"
