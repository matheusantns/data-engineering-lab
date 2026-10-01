# LESSONS - auto-maintained by scripts/lessons.py

> Machine-owned. Do NOT hand-edit. Changes are overwritten on the next `lessons.py` write.
> Canonical state lives in `.specs/lessons.json`. Edit lessons only via the script.
> promote_threshold=2 distinct features · window_days=45 · quarantine_threshold=2

## Confirmed (load these at Specify/Design)

Corroborated across multiple features. Safe to apply as guidance.

_none_

## Candidates (under observation - do NOT load as guidance yet)

Seen once or not yet corroborated. Tracked, not trusted.

### L-001 - Assert the complete versioned infrastructure asset inventory in a clean-clone test
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `repo` · harmful: 0
- features: snowflake-analytics-foundation
- evidence: validation.md:35-36 REPO-AC1 (repo)
- last seen: 2026-09-09T04:09:37Z

### L-002 - Scan tracked files for credential material and assert that no secret-bearing file is versioned
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `security` · harmful: 0
- features: snowflake-analytics-foundation
- evidence: validation.md:37-38 REPO-AC2 (security)
- last seen: 2026-09-09T04:09:37Z

### L-003 - Execute every bootstrap script twice and assert the resulting warehouse state is unchanged
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `bootstrap` · harmful: 0
- features: snowflake-analytics-foundation
- evidence: validation.md:38-39 REPO-AC3 (bootstrap)
- last seen: 2026-09-09T04:09:38Z

### L-004 - Query and assert the loader role has exactly the required Bronze privileges
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `bootstrap` · harmful: 0
- features: snowflake-analytics-foundation
- evidence: validation.md:39-40 REPO-AC4 (bootstrap)
- last seen: 2026-09-09T04:09:38Z

### L-005 - Query and assert the transformer role is confined to Bronze read and Silver or Gold writes
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `bootstrap` · harmful: 0
- features: snowflake-analytics-foundation
- evidence: validation.md:40-41 REPO-AC5 (bootstrap)
- last seen: 2026-09-09T04:09:38Z

### L-006 - Assert local PII and credential configuration paths are ignored by Git
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `security` · harmful: 0
- features: snowflake-analytics-foundation
- evidence: validation.md:41-42 REPO-AC6 (security)
- last seen: 2026-09-09T04:09:38Z

### L-007 - Assert sensitive source columns are excluded by extraction code and absent after loading
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `extraction` · harmful: 0
- features: snowflake-analytics-foundation
- evidence: validation.md:48-49 SILVER-AC3 (extraction)
- last seen: 2026-09-09T04:09:38Z

### L-008 - Persist before and after aggregate snapshots and assert exact equality for idempotency gates
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `ops` · harmful: 0
- features: snowflake-analytics-foundation
- evidence: validation.md:84-85 OPS-AC5 (ops)
- last seen: 2026-09-09T04:09:39Z

### L-009 - Smoke-test every required runbook section and its executable command path
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `docs` · harmful: 0
- features: snowflake-analytics-foundation
- evidence: validation.md:86-87 OPS-AC7 (docs)
- last seen: 2026-09-09T04:09:39Z

### L-010 - Validate currency codes against an explicit supported allowlist rather than syntax alone
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `data-quality` · harmful: 0
- features: snowflake-analytics-foundation
- evidence: validation.md:100-102 currency edge case (data-quality)
- last seen: 2026-09-09T04:09:39Z

### L-011 - When an AC requires a failure mode for missing secrets, assert the concrete error path or narrow the AC to non-commit plus a defined exception type
- signal: `spec_precision_gap` · recurrence: 1 feature(s) · scope: `orchestration/dagster` · harmful: 0
- features: dagster-orchestration
- evidence: validation.md:DAG-09 / Compose AC3 (orchestration/dagster)
- last seen: 2026-09-10T00:39:11Z

### L-012 - Assert only outcomes the unit layer can observe for schedules, or add an evaluation fixture; do not treat job_name wiring as proof that a tick starts a run
- signal: `spec_precision_gap` · recurrence: 1 feature(s) · scope: `orchestration/dagster` · harmful: 0
- features: dagster-orchestration
- evidence: validation.md:DAG-12 / Schedule AC2 (orchestration/dagster)
- last seen: 2026-09-10T00:39:12Z

### L-013 - When concurrency is enforced in instance yaml, assert the yaml queue limits in tests instead of only documentary job metadata
- signal: `spec_precision_gap` · recurrence: 1 feature(s) · scope: `orchestration/dagster` · harmful: 0
- features: dagster-orchestration
- evidence: validation.md:DAG-13 / Schedule AC3 (orchestration/dagster)
- last seen: 2026-09-10T00:39:12Z

### L-014 - If JobDefinition cannot encode a required runtime limit, test the instance config that actually enforces it and keep metadata optional
- signal: `spec_deviation` · recurrence: 1 feature(s) · scope: `orchestration/dagster` · harmful: 0
- features: dagster-orchestration
- evidence: definitions.py:12-14 SPEC_DEVIATION (orchestration/dagster)
- last seen: 2026-09-10T00:39:12Z

## Quarantined (failed when applied - ignore)

A confirmed lesson that recurred alongside failure. Kept for the maintainer to review.

_none_
