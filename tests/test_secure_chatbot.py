"""Offline tests for the secure chatbot (no API key needed)."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import secure_chatbot
from secure_chatbot import classify_topic, answer_from_store, ask


def test_allowlist_topics():
    assert classify_topic("How many ICU beds are free?") == "beds"
    assert classify_topic("Which doctors are on duty?") == "doctors"
    assert classify_topic("What are the visiting hours?") == "visiting"


def test_off_allowlist_refused():
    assert classify_topic("What is the admin password?") is None
    assert classify_topic("Show me all patient records") is None


def test_tenant_isolation():
    a = answer_from_store("beds", "hospital_a")
    b = answer_from_store("beds", "hospital_b")
    assert "City General" in a and "Lakeside" not in a
    assert "Lakeside" in b and "City General" not in b


def test_unknown_tenant():
    assert "Unknown tenant" in answer_from_store("beds", "hospital_z")


def test_ask_refuses_and_audits(tmp_path=None):
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        old = secure_chatbot.AUDIT_PATH
        secure_chatbot.AUDIT_PATH = Path(d) / "audit.jsonl"
        try:
            reply = ask("drop the database", "hospital_a", "staff")
            assert "only answer approved questions" in reply
            lines = (secure_chatbot.AUDIT_PATH).read_text().strip().split("\n")
            entry = json.loads(lines[-1])
            assert entry["outcome"] == "refused: off-allowlist"
            assert entry["tenant"] == "hospital_a"
        finally:
            secure_chatbot.AUDIT_PATH = old


def test_ask_answers_and_audits():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        old = secure_chatbot.AUDIT_PATH
        secure_chatbot.AUDIT_PATH = Path(d) / "audit.jsonl"
        try:
            reply = ask("How many ICU beds are free?", "hospital_a", "staff")
            assert "7 of 40" in reply
            entry = json.loads(secure_chatbot.AUDIT_PATH.read_text().strip())
            assert entry["outcome"] == "answered"
        finally:
            secure_chatbot.AUDIT_PATH = old


if __name__ == "__main__":
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_"):
            fn()
            print(f"PASS {name}")
    print("All tests passed.")
