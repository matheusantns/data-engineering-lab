# Fundação Analítica Snowflake Validation

**Result**: FAIL
**Date**: 2026-09-09
**Spec**: `.specs/features/snowflake-analytics-foundation/spec.md`
**Requested final task commit**: `354a6f8`
**Complete feature range**: `a7e3be7..354a6f8` (`24b8cac^..354a6f8`, 55 commits, 104 files)
**Verifier**: independent sub-agent (author != verifier)
**Current repository state**: clean porcelain at sensor baseline and cleanup; `HEAD` moved concurrently to `115b2bd` after dispatch and deletes `dw/snowflake/analytics/tests/test_readme.py`.

## Executive Result

- Acceptance criteria: 28/37 matched to assertion-level evidence; 9/37 are evidence-zero gaps.
- Edge cases: 7/8 matched; the unknown-but-well-formed currency case is not rejected.
- Gates at requested final commit: dbt docs 1/1; unchanged-Bronze runner builds 384/384; Python 100/100 (93 analytics, including 5 README smoke tests, plus 7 runner tests).
- Discrimination sensor: 5 injected, 5 killed, 0 survived.
- Completion gate cannot pass because this report is correctly FAIL.

## Task Completion and Commit Integrity

- `tasks.md` defines 41 task bodies, not T1-T42. T9 is absent between `tasks.md:203-219` and `tasks.md:222-238`, although phase diagrams claim T9 at `tasks.md:49-53,795-800`.
- All 162 visible Done-when checkboxes are checked, but there is no T9 definition, Tests, Gate, Done-when evidence, or atomic task commit.
- The range starts at T1 commit `24b8cac` and ends at T42 commit `354a6f8`. It contains 55 commits. Several task commits do not use the planned Conventional Commit messages, and unrelated root README/todo changes are mixed into the feature range.
- `design.md` is ignored by `.gitignore:18` and absent from `git ls-files`; a clean clone cannot recover this approved source-of-truth artifact.
- Requirement traceability is stale: `spec.md:158-177` still contains `In Tasks` and `In Progress` statuses after claimed completion. Goals and success criteria remain unchecked at `spec.md:7-12,182-190`.
- Test-file integrity was positive at `354a6f8`: 0 baseline scoped test files and 41 final scoped test files. Concurrent commit `115b2bd` then deleted `test_readme.py`, reducing the current count to 40 and removing five smoke tests.

## Spec-Anchored Acceptance Criteria

Evidence follows the evidence-or-zero rule. Source code, a checked task box, or a successful manual command is recorded as supporting evidence but does not replace the required `file:line` assertion.

### P1: Código Snowflake versionado e seguro

| AC | Spec-defined outcome | Assertion evidence | Result |
| --- | --- | --- | --- |
| REPO-AC1 | Git contains database, schema, role, grant scripts and dbt project | No scoped test assertion enumerates all required versioned assets; `test_readme.py:79-81` only asserted three documentation links before its deletion | GAP |
| REPO-AC2 | No password, private key, token, or credential file is tracked | No `file:line` test assertion. Independent `git check-ignore` and tracked-marker scan passed | GAP |
| REPO-AC3 | Reapplying infrastructure reaches the same state without object-exists failure | No assertion-level bootstrap integration test; `bootstrap/001_database.sql:1`, `002_roles.sql:1-2`, and `003_schemas.sql:1-3` use `IF NOT EXISTS`, but grants/users lack an executed reapplication assertion | GAP |
| REPO-AC4 | Loader has only privileges required to write Bronze | No privilege-test assertion. Grants are declared at `bootstrap/004_grants.sql:1-9` | GAP |
| REPO-AC5 | Transformer reads Bronze and creates/updates only Silver and Gold | No privilege-test assertion. Grants are declared at `bootstrap/004_grants.sql:11-45` | GAP |
| REPO-AC6 | Local configuration containing PII or credentials is ignored | No assertion-level test. Ignore rules exist at `.gitignore:8-16` and the independent ignore check passed | GAP |

### P1: Silver source-conformed

| AC | Spec-defined outcome | `file:line` assertion | Result |
| --- | --- | --- | --- |
| SILVER-AC1 | 16 Bronze tables produce 16 Silver views | `test_ecommerce_sources.py:107-108` `assertEqual(len(listed_sources), 16)` and exact source-name set; `test_stg_inventory_movements.py:150` `assertEqual(len(silver_views), 16)`; integrated build created 16 views | PASS |
| SILVER-AC2 | Silver users excludes `password_hash` | `test_stg_users.py:99` `assertNotIn("password_hash", raw_code)` | PASS |
| SILVER-AC3 | Bronze extraction excludes `password_hash` | No test assertion exercises `ecommerce_bronze_pipeline.py:25-27`; full extraction was unavailable because PostgreSQL rejected local authentication | GAP |
| SILVER-AC4 | Natural keys, grain, and source semantics are preserved | Per-model exact source/materialization and grain assertions, including `test_stg_users.py:67-87`, `test_stg_cart_items.py:94-121`, `test_stg_order_items.py:90-117`, and `test_stg_inventory_movements.py:89-135` | PASS |
| SILVER-AC5 | Analytical timestamps are UTC | Exact conversion assertions across models, including `test_stg_users.py:92-96`, `test_stg_orders.py:79-82`, `test_stg_payments.py:77-80`, and `test_stg_shipments.py:79-82` | PASS |
| SILVER-AC6 | Every primary key is unique and non-null | Exact generic-test assertions across 16 model tests, e.g. `test_stg_users.py:87` `assertEqual(tests, {"not_null", "unique"})`; all corresponding dbt tests passed | PASS |
| SILVER-AC7 | Gold-used foreign keys are relationship-tested | Parent-node assertions include `test_stg_addresses.py:98-103`, `test_stg_order_items.py:90-99`, `test_stg_payments.py:97-106`, and `test_stg_shipments.py:99-109`; dbt relationship tests passed | PASS |
| SILVER-AC8 | Order/payment statuses use exact accepted domains | `test_stg_orders.py:134` exact order-status list; `test_stg_payments.py:120` exact provider/status dictionaries | PASS |
| SILVER-AC9 | Critical Silver failure stops Gold completion | `test_run_daily.py:130-132` asserts dbt failure exit 23 and logged cause; `dbt_project.yml:9-12` makes warnings fatal; integrated DAG build passed | PASS |

### P1: Gold dimensional de vendas

| AC | Spec-defined outcome | `file:line` assertion | Result |
| --- | --- | --- | --- |
| GOLD-AC1 | Type-1 date, customer, and product dimensions are built | Exact dbt unit expected rows at `dim_date.yml:49-52`, `dim_customer.yml:45-49`, and `dim_product.yml:97-101`; all unit tests passed | PASS |
| GOLD-AC2 | One fact row per order | `fct_orders.yml:131-138` expects one row for each of six input orders; `fct_orders.yml:10-15` declares unique/non-null `order_id` tests | PASS |
| GOLD-AC3 | One item fact row per order and variant | `fct_order_items.yml:110-114` expects three distinct order/product rows; `fct_order_items.yml:9-13` asserts the composite unique grain | PASS |
| GOLD-AC4 | Customer dimension excludes direct name/email/phone/address | `test_assert_gold_has_no_direct_pii.py:71-83` exact prohibited mutation list; `dim_customer.yml:45-49` expected payload contains only non-PII state | PASS |
| GOLD-AC5 | Product dimension supports product, variant, direct category | `dim_product.yml:97-101` exact expected product, variant, and category values | PASS |
| GOLD-AC6 | Date derives UTC day, month, quarter, year | `dim_date.yml:49-52` exact keys and calendar attributes, including ISO week/day | PASS |
| GOLD-AC7 | Order fact exposes required financial measures, status, currency | `fct_orders.yml:133-138` exact expected payload values for all required fields | PASS |
| GOLD-AC8 | Item fact exposes qty, unit price, discount, line total, capture flag | `fct_order_items.yml:112-114` exact expected payload values | PASS |
| GOLD-AC9 | Recognized revenue is captured-payment sum | `fct_orders.yml:133-138` expects 100 for one capture, 100 for two captures, and zero otherwise; `test_assert_captured_revenue_reconciles.py:68-111` asserts valid and violating result sets | PASS |
| GOLD-AC10 | Financial metrics remain partitioned by currency | `test_assert_supported_currencies.py:113-129` exact USD/EUR mismatch results; `:138-143` asserts currency remains in order/item aggregation SQL | PASS |
| GOLD-AC11 | Five metrics are derivable without Bronze joins | At requested final commit, `test_readme.py:111` `assertEqual(rows, METRIC_ROWS)` asserted all five definitions and grains. Concurrent commit `115b2bd` deleted this assertion | PASS at `354a6f8`; regression after range |
| GOLD-AC12 | Fact grains and dimension references are tested | Generic unique/relationship declarations at `fct_orders.yml:10-35` and `fct_order_items.yml:9-52`; all dbt tests passed | PASS |
| GOLD-AC13 | `subtotal - discount + shipping = total` | `test_assert_order_totals_reconcile.py:44-59` asserts valid `[]` and mutant `[(2,)]`; `:65` asserts explicit `decimal(12,2)` precision | PASS |
| GOLD-AC14 | Recognized revenue reconciles to captured payments | `test_assert_captured_revenue_reconciles.py:68-111` exact valid and mutant failure sets by currency | PASS |

### P1: Operação manual diária

| AC | Spec-defined outcome | `file:line` assertion | Result |
| --- | --- | --- | --- |
| OPS-AC1 | Bronze runs before Silver/Gold | `test_run_daily.py:100` `assertEqual(events, ["bronze", "dbt"])` | PASS |
| OPS-AC2 | Bronze failure prevents dbt | `test_run_daily.py:123-125` asserts exit 17, events `["bronze"]`, and logged cause | PASS |
| OPS-AC3 | Successful Bronze invokes dependency-ordered dbt build | `test_run_daily.py:106-108` asserts `build`, project dir, and profiles dir arguments | PASS |
| OPS-AC4 | Critical failure returns nonzero and records cause | `test_run_daily.py:130-132` asserts exit 23, both steps, and exact dbt-failure message | PASS |
| OPS-AC5 | Unchanged rerun produces identical Gold counts and sums by currency | Two `-SkipExtract` builds each passed 192/192, but no persisted `file:line` assertion or independently retained before/after snapshot proves equality. The supplied byte-identical values are not present in repository evidence | GAP |
| OPS-AC6 | Concurrent second run is refused | `test_run_daily.py:140-143` asserts nonzero, no steps, unchanged lock content, and `already in progress` | PASS |
| OPS-AC7 | Runbook covers setup, daily execution, validation, diagnosis, rerun | No scoped smoke-test assertion validates these required sections; README link coverage at former `test_readme.py:79-81` is insufficient | GAP |
| OPS-AC8 | Logs and dbt artifacts are local and ignored | `test_run_daily.py:114-118` asserts one log with start/build/success records; independent `git check-ignore` passed for `logs/`, `target/`, and lock paths | PASS |

**Acceptance status**: 28 PASS, 9 GAP, 0 precision-only warnings.

## Edge Cases

| Edge case | Evidence | Result |
| --- | --- | --- |
| Empty Bronze creates valid relations without fabricated sales | Empty expected rows at `dim_date.yml:55-61`, `dim_customer.yml:51-58`, `dim_product.yml:103-114`, `fct_orders.yml:140-149`, and `fct_order_items.yml:116-125` | PASS |
| No captured payment gives zero recognized revenue | `fct_orders.yml:134-135,138` exact `recognized_revenue: 0.00` | PASS |
| Refunded payment is excluded from revenue and included in refund | `fct_orders.yml:136` exact revenue 0 and refund 25 | PASS |
| Multiple captures are summed without item duplication | `fct_orders.yml:137` exact captured sum/count; `fct_order_items.yml:110-114` exact three-row payload | PASS |
| Product hierarchy preserves direct category without recursive expansion | `dim_product.yml:97-101` exact direct category payload | PASS |
| Missing critical dimension key fails before build completion | Relationship declarations at `fct_order_items.yml:16-52` plus runner nonzero propagation at `test_run_daily.py:130-132` | PASS |
| Unrecognized currency fails rather than mixing | `assert_supported_currencies.sql:32-33` rejects only null or non-`^[A-Z]{3}$` values. A well-formed unknown code such as `AAA` survives; the spec does not define an allowlist | FAIL |
| Snowflake unavailable fails without completion | `test_run_daily.py:130-132` asserts dbt nonzero and failure message; success marker is only asserted on happy path at `:118` | PASS |

## Final Gates

| Gate | Command/outcome | Result |
| --- | --- | --- |
| dbt docs | `.venv\Scripts\dbt.exe docs generate --project-dir dw\snowflake\analytics --profiles-dir dw\snowflake\analytics`; found 21 models, 161 data tests, 16 sources, 10 unit tests; wrote `catalog.json` | PASS 1/1 |
| Runner build 1 | `run_daily.ps1 -SkipExtract` with `.venv\Scripts` on PATH | PASS 192/192 |
| Runner build 2 | same unchanged-Bronze command | PASS 192/192 |
| Python analytics | `.venv\Scripts\python.exe -m unittest discover -s dw\snowflake\analytics\tests -p "test_*.py"` begun at requested final state | PASS 93/93 in 220.407s |
| Python runner | `.venv\Scripts\python.exe -m unittest discover -s dw\snowflake\scripts -p "test_*.py"` | PASS 7/7 in 3.577s |
| Full Bronze extraction | Not rerun: PostgreSQL local authentication is definitively unavailable | BLOCKED, accurately limited |

The initial runner attempt failed because `dbt` was absent from PATH. With the documented `.venv\Scripts` directory added, both runs exited 0. This configuration failure is not counted as a product failure.

## Discrimination Sensor

Scratch was a detached temporary worktree pinned to `354a6f8`. Every mutant was run independently after resetting the scratch.

| # | Mutation | Killing assertion | Result |
| --- | --- | --- | --- |
| 1 | `fct_orders.sql:4` captured revenue status `captured` -> `authorized` | `fct_orders.yml:133,137` exact recognized revenue | KILLED, dbt unit exit 1 |
| 2 | `fct_orders.sql:5` refunded status `refunded` -> `failed` | `fct_orders.yml:135-136` exact failed/refunded outcomes | KILLED, dbt unit exit 1 |
| 3 | `fct_order_items.sql:7` capture flag `> 0` -> `>= 0` | `fct_order_items.yml:114` exact `has_captured_payment: false` | KILLED, dbt unit exit 1 |
| 4 | `assert_gold_has_no_direct_pii.sql:30-33` removed email detection | `test_assert_gold_has_no_direct_pii.py:71-83` exact five-category list | KILLED, Python exit 1 |
| 5 | `assert_supported_currencies.sql:33` allowed lowercase codes | `test_assert_supported_currencies.py:97-105` exact invalid-code list | KILLED, Python exit 1 |

**Sensor depth**: expanded security/data-integrity.
**Result**: 5 injected, 5 killed, 0 survived.
**Isolation**: scratch removed and pruned. Real-tree porcelain was empty before sensor work and empty after cleanup. Concurrent commit movement changed `HEAD`, not porcelain, and was not caused by the verifier.

## Code Quality and Traceability

| Check | Result |
| --- | --- |
| Minimum/surgical implementation | FAIL: 55-commit range contains unrelated root README/todo changes |
| No unnecessary flexibility | PASS for transformation models |
| Existing dbt and repository patterns | PASS |
| Spec-anchored payload assertions | PASS for Gold; FAIL for security/bootstrap/extraction/runner-idempotency/runbook gaps |
| Per-layer coverage | FAIL: no assertion-level bootstrap privilege/idempotency tests and no extraction test |
| Every scoped test claimed | PASS at `354a6f8` |
| Test integrity | FAIL on current `HEAD`: concurrent deletion removed five README smoke tests |
| Requirement traceability | FAIL: T9 missing, statuses stale, approved design ignored/untracked |
| Guidelines | `coding-principles.md` and `design.md` reviewed |

## Ranked Gaps

1. **Completion structure is invalid**: T9 does not exist, despite the claim that T1-T42 are complete. Traceability remains stale.
2. **Nine ACs have zero assertion-level evidence**: six repository/security/bootstrap criteria, Bronze `password_hash` exclusion, exact no-change snapshot equality, and runbook completeness.
3. **Unknown ISO-shaped currencies are accepted**: `AAA` passes the format-only test, violating the edge-case wording.
4. **Test integrity regressed after dispatch**: `115b2bd` deleted five README smoke tests and reduced scoped test files from 41 to 40.
5. **Approved design is not reproducible from Git**: `design.md` is ignored and untracked.
6. **Feature history is not atomic/surgical**: the 55-commit range includes unrelated changes and several non-Conventional task commits.

## Summary

**Overall**: FAIL. Runtime transformation gates and the expanded sensor are strong, but evidence-zero acceptance gaps, the missing T9 definition, the currency behavior defect, stale traceability, the untracked design, and the post-dispatch test deletion prevent full-feature acceptance.
