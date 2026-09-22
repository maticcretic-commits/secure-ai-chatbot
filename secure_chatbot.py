#!/usr/bin/env python3
"""
Secure AI Chatbot — portfolio practice project.

Starter for the "secure, tenant-aware AI assistant" gig pattern
(e.g. a registry app where each hospital sees only its own data).

Security rules baked in (the interesting part of this demo):
  * Every request carries tenant_id + role — data is ALWAYS filtered
    by tenant before anything else happens.
  * Only allowlisted question topics are answered; anything else is
    refused (no open-ended SQL, no model-generated queries at all).
  * Read-only "tools": plain Python functions over an in-memory store.
  * Every query is appended to audit_log.jsonl (who asked what, when).

Usage:
    pip install -r requirements.txt
    cp .env.example .env   # add OPENAI_API_KEY
    python secure_chatbot.py --tenant hospital_a --role staff \
        --ask "How many ICU beds are free?"
    python tests/test_secure_chatbot.py   # no API key needed
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA_PATH = BASE / "data" / "tenant_data.json"
AUDIT_PATH = BASE / "audit_log.jsonl"

# Only these topics may be answered. Everything else -> refusal.
ALLOWLIST = {
    "beds": ["bed", "icu", "capacity", "free", "available bed"],
    "doctors": ["doctor", "physician", "staff on", "on duty"],
    "visiting": ["visit", "visiting hour", "visitor"],
}

# TODO(learn): add per-role topic restrictions, e.g. only 'admin' may ask
# about staff details. Then write a test proving it.


def load_store():
    return json.loads(DATA_PATH.read_text())


def classify_topic(question):
    q = question.lower()
    for topic, keywords in ALLOWLIST.items():
        if any(k in q for k in keywords):
            return topic
    return None


def answer_from_store(topic, tenant_id):
    """Read-only lookup, tenant-scoped. No SQL, no model-generated queries."""
    store = load_store()
    tenant = store.get(tenant_id)
    if tenant is None:
        return "Unknown tenant."
    data = tenant.get(topic)
    if data is None:
        return "No data for that topic."
    if topic == "beds":
        return (f"{tenant['name']}: {data['free']} of {data['total']} "
                f"ICU beds currently free.")
    if topic == "doctors":
        return f"Doctors on duty at {tenant['name']}: {', '.join(data)}."
    if topic == "visiting":
        return f"Visiting hours at {tenant['name']}: {data}."
    return "No data for that topic."


def audit(tenant_id, role, question, topic, outcome):
    entry = {"at": datetime.utcnow().isoformat(), "tenant": tenant_id,
             "role": role, "question": question, "topic": topic,
             "outcome": outcome}
    with open(AUDIT_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def ask(question, tenant_id, role, use_ai=False):
    topic = classify_topic(question)
    if topic is None:
        audit(tenant_id, role, question, None, "refused: off-allowlist")
        return ("I can only answer approved questions about beds, doctors on "
                "duty, and visiting hours.")
    base = answer_from_store(topic, tenant_id)
    audit(tenant_id, role, question, topic, "answered")
    if not use_ai:
        return base
    try:
        from openai import OpenAI
        import os
    except ImportError:
        sys.exit("pip install openai (or drop --ai)")
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.exit("Set OPENAI_API_KEY (see .env.example) or drop --ai.")
    client = OpenAI(api_key=key)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system",
             "content": ("Rephrase the given fact politely. Do not add new "
                         "facts. If the fact says 'Unknown tenant', reply "
                         "that you cannot help.")},
            {"role": "user", "content": f"Fact: {base}\nQuestion: {question}"},
        ],
    )
    return resp.choices[0].message.content


def main():
    p = argparse.ArgumentParser(description="Tenant-aware secure chatbot")
    p.add_argument("--tenant", required=True, help="tenant id, e.g. hospital_a")
    p.add_argument("--role", default="staff", help="caller role")
    p.add_argument("--ask", required=True, help="question in quotes")
    p.add_argument("--ai", action="store_true", help="polish answer with OpenAI")
    args = p.parse_args()
    print(ask(args.ask, args.tenant, args.role, use_ai=args.ai))


if __name__ == "__main__":
    main()
