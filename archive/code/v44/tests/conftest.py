import json
from pathlib import Path
import pytest
from evorationale.model import normalize_history, validate_state

ROOT = Path(__file__).resolve().parent.parent

@pytest.fixture
def state():
    return json.loads((ROOT/'examples/redis/decision_state.json').read_text())

@pytest.fixture
def raw_history():
    return [json.loads(x) for x in (ROOT/'examples/redis/history.jsonl').read_text().splitlines() if x.strip()]

@pytest.fixture
def approved_state(state):
    return validate_state(state)

@pytest.fixture
def history(raw_history):
    return normalize_history(raw_history)
