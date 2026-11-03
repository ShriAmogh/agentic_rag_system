import pytest
from langgraph_agents.graph import entry_router, router, generate_router, MAX_ATTEMPTS


def test_entry_router():
    assert entry_router({"mode": "compare"}) == "compare"
    assert entry_router({"mode": "discover"}) == "rag"
    assert entry_router({"mode": "chat"}) == "rag"
    assert entry_router({}) == "rag"


def test_generate_router():
    assert generate_router({"mode": "chat"}) == "audit"
    assert generate_router({"mode": "discover"}) == "evaluate"
    assert generate_router({}) == "evaluate"


def test_router_success_moves_to_audit():
    # When evaluation_errors is None, proceed to audit
    state = {"mode": "discover", "evaluation_errors": None, "attempts": 1}
    assert router(state) == "audit"


def test_router_error_triggers_retry():
    # When evaluation_errors present and attempts < MAX_ATTEMPTS, retry
    state = {"mode": "discover", "evaluation_errors": "Validation error in schema", "attempts": 1}
    assert router(state) == "retry"


def test_router_prevents_infinite_loop_at_max_attempts():
    # When attempts reaches MAX_ATTEMPTS (3), force forward to audit
    state = {"mode": "discover", "evaluation_errors": "Still failing schema", "attempts": MAX_ATTEMPTS}
    assert router(state) == "audit"

    state_over = {"mode": "discover", "evaluation_errors": "Error", "attempts": MAX_ATTEMPTS + 1}
    assert router(state_over) == "audit"


def test_router_chat_mode_always_audit():
    state = {"mode": "chat", "evaluation_errors": "Some error", "attempts": 1}
    assert router(state) == "audit"

