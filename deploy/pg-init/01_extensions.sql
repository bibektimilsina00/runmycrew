-- ─── First-boot extension setup ────────────────────────────────────────
-- Runs ONCE, the very first time the Postgres data volume is empty —
-- official Postgres image semantics. Idempotent regardless thanks to
-- `IF NOT EXISTS`, but the Alembic migrations also create what they
-- need on first run; this file is belt-and-suspenders.
-- ───────────────────────────────────────────────────────────────────────

CREATE EXTENSION IF NOT EXISTS vector;
