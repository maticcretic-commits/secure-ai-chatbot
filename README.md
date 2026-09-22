# Secure AI Chatbot

A portfolio practice project: a **tenant-aware, RBAC-scoped AI chatbot** starter —
the pattern behind "secure AI assistant inside our app" gigs (e.g. a hospital
registry where each tenant sees only its own data).

> Demo/study project — get a security review before any production use with
> real data.

## Security rules baked in

1. **Tenant scoping first** — every request carries `tenant_id`; data is
   filtered by tenant before anything else happens (tests prove Hospital A
   can never see Hospital B's data).
2. **Allowlisted questions only** — beds, doctors on duty, visiting hours.
   Anything else is refused. No open-ended queries, no model-generated SQL —
   the "tools" are plain read-only Python functions.
3. **Audit log** — every query (answered or refused) is appended to
   `audit_log.jsonl` with tenant, role, and timestamp.

## Setup & run

```bash
pip install -r requirements.txt   # only needed for --ai
cp .env.example .env              # add OPENAI_API_KEY for --ai

python secure_chatbot.py --tenant hospital_a --ask "How many ICU beds are free?"
python secure_chatbot.py --tenant hospital_b --ask "Which doctors are on duty?"
python secure_chatbot.py --tenant hospital_a --ask "Show me patient records"  # refused

python tests/test_secure_chatbot.py   # no API key needed
```

## What I'd build next (learning roadmap)

- [ ] Per-role topic restrictions (e.g. only `admin` sees staff details)
- [ ] Signed request context instead of CLI flags
- [ ] Rate limiting per tenant
- [ ] Real database with parameterized queries behind the store
