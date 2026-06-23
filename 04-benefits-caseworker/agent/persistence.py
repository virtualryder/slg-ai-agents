# agent/persistence.py
def get_checkpointer():
    from langgraph.checkpoint.memory import MemorySaver
    return MemorySaver()
