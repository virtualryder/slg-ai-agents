import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent

# Only add platform_core and the repo root — NOT any specific agent directory.
# Each agent's tests prepend their own directory via sys.path manipulation.
for p in (_ROOT / "platform_core", _ROOT):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)


# ---------------------------------------------------------------------------
# Module-isolation hook: agents 01-08 (and their aws-native counterparts) all
# define packages named `agent`, `tools`, and top-level `core`.  Python caches
# modules in sys.modules, so whichever agent's code is imported first wins for
# the entire test run.  This hook purges those cached modules whenever pytest
# moves to a test file in a different agent directory, so each agent's tests
# import their own code.
# ---------------------------------------------------------------------------
_AGENT_MODULE_PREFIXES = ("agent", "tools", "core")
_last_agent_dir: str | None = None


def _agent_dir_for(fspath: str) -> str | None:
    """Return the agent root directory for a test file, or None."""
    p = Path(fspath).resolve()
    for parent in p.parents:
        if parent.name.startswith(("0", "wog")) and parent.parent in (_ROOT, _ROOT / "aws-native-reference"):
            return str(parent)
    return None


def _flush_and_set(agent_dir: str) -> None:
    """Purge cached agent/tools/core modules and prepend *agent_dir* to sys.path."""
    global _last_agent_dir
    _last_agent_dir = agent_dir
    to_remove = [k for k in sys.modules
                 if any(k == pfx or k.startswith(pfx + ".")
                        for pfx in _AGENT_MODULE_PREFIXES)]
    for k in to_remove:
        del sys.modules[k]
    # Put this agent's directory at the very front of sys.path
    if agent_dir in sys.path:
        sys.path.remove(agent_dir)
    sys.path.insert(0, agent_dir)


def pytest_collect_file(parent, file_path):
    """Flush stale agent modules when collecting a file in a new agent dir."""
    agent_dir = _agent_dir_for(str(file_path))
    if agent_dir and agent_dir != _last_agent_dir:
        _flush_and_set(agent_dir)


def pytest_runtest_setup(item):
    """Flush stale agent modules again right before each test executes,
    so imports inside test function bodies resolve to the correct agent."""
    agent_dir = _agent_dir_for(str(item.fspath))
    if agent_dir and agent_dir != _last_agent_dir:
        _flush_and_set(agent_dir)
