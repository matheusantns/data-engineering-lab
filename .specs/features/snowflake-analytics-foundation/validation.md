# Fundação Analítica Snowflake — Interim Validation T23–T29

**Date**: 2026-09-07  
**Scope**: delivery group T23–T29 only; this is not completion evidence for T30–T42  
**Spec**: `.specs/features/snowflake-analytics-foundation/spec.md`  
**Design**: `.specs/features/snowflake-analytics-foundation/design.md`  
**Diff range**: `6ca337d..1ce5e8a`  
**Commits**: `b538755`, `62314f0`, `1a09ed1`, `7be8365`, `d5f96f4`, `3271435`, `1ce5e8a`  
**Verifier**: independent sub-agent (author ≠ verifier)  
**Verdict**: **PASS**

This report verifies the seven transactional Silver models delivered by T23–T29. It intentionally does not run `validate_state.py` or claim full-feature completion because T30–T42 remain pending.

## Task Completion

| Task | Status | Done-when coverage |
| --- | --- | --- |
| T23 — cart items | PASS | 4/4 |
| T24 — orders | PASS | 5/5 |
| T25 — order items | PASS | 4/4 |
| T26 — order status history | PASS | 4/4 |
| T27 — payments | PASS | 5/5 |
| T28 — shipments | PASS | 4/4 |
| T29 — inventory movements | PASS | 4/4 |

**Total**: 30/30 Done-when criteria passed.

## Done-When Evidence

### T23 — Cart items

1. **Unique grain `cart_id, variant_id`** — `dw/snowflake/analytics/tests/test_stg_cart_items.py:105-121` asserts both `"group by cart_id, variant_id"` and `"having count(*) > 1"`. The executed rejection query is `dw/snowflake/analytics/tests/assert_stg_cart_items_grain.sql:1-6`:
   `select cart_id, variant_id ... group by cart_id, variant_id having count(*) > 1`.
2. **Both foreign keys valid and required** — `dw/snowflake/analytics/tests/test_stg_cart_items.py:83-103` asserts, for both `cart_id` and `variant_id`, the exact test set `{"not_null", "relationships"}` and the exact parents `stg_carts` and `stg_product_variants`. Definitions are at `dw/snowflake/analytics/models/silver/stg_cart_items.yml:7-23`.
3. **Quantity greater than zero** — `dw/snowflake/analytics/tests/test_stg_cart_items.py:123-128` asserts `"where qty <= 0"`. The executed rejection predicate is `dw/snowflake/analytics/tests/assert_stg_cart_items_qty_positive.sql:3`: `where qty <= 0`, exactly matching the source check `qty > 0` at `erp/sample-postgres/init/01-ecommerce.sql:148`.
4. **Focused build passes** — superseded by the stronger full integrated gate: model `stg_cart_items` and all dependent tests passed within PASS 118.

### T24 — Orders

1. **`order_id` and `order_number` unique and non-null** — `dw/snowflake/analytics/tests/test_stg_orders.py:84-101` asserts the exact mapping `{"order_id": {"not_null", "unique"}, "order_number": {"not_null", "unique"}}`; definitions are at `dw/snowflake/analytics/models/silver/stg_orders.yml:7-26`.
2. **User references users** — `dw/snowflake/analytics/tests/test_stg_orders.py:103-126` asserts the `user_id` relationship depends on `model.snowflake_analytics.stg_users` and includes `not_null`; definition is at `dw/snowflake/analytics/models/silver/stg_orders.yml:13-20`.
3. **Status accepts only source values** — `dw/snowflake/analytics/tests/test_stg_orders.py:127-138` asserts the exact list `["pending", "paid", "processing", "shipped", "delivered", "cancelled"]`, matching `erp/sample-postgres/init/01-ecommerce.sql:161-163`.
4. **Non-negative values and UTC timestamps** — `dw/snowflake/analytics/tests/test_stg_orders.py:140-153` asserts each exact rejection expression: `"subtotal < 0"`, `"discount_total < 0"`, `"shipping_total < 0"`, and `"grand_total < 0"`. The executed SQL is `dw/snowflake/analytics/tests/assert_stg_orders_values_nonnegative.sql:1-6`. `dw/snowflake/analytics/tests/test_stg_orders.py:77-82` asserts `convert_timezone('utc', <source>) as <source>_utc` for `ordered_at`, `created_at`, and `updated_at`.
5. **Focused build passes** — superseded by the full integrated gate; model and tests passed within PASS 118.

### T25 — Order items

1. **Unique grain `order_id, variant_id`** — `dw/snowflake/analytics/tests/test_stg_order_items.py:101-117` asserts `"group by order_id, variant_id"` and `"having count(*) > 1"`. The rejection query is `dw/snowflake/analytics/tests/assert_stg_order_items_grain.sql:1-6`.
2. **Both foreign keys valid and required** — `dw/snowflake/analytics/tests/test_stg_order_items.py:78-99` asserts exact test set `{"not_null", "relationships"}` and exact parents `stg_orders` and `stg_product_variants`; definitions are at `dw/snowflake/analytics/models/silver/stg_order_items.yml:7-23`.
3. **Quantity, price, discount, and line total limits** — `dw/snowflake/analytics/tests/test_stg_order_items.py:119-132` asserts the exact rejection expressions `"qty <= 0"`, `"unit_price < 0"`, `"discount < 0"`, `"discount > 1"`, and `"line_total < 0"`. The executed predicate is `dw/snowflake/analytics/tests/assert_stg_order_items_limits.sql:3-7`, matching source constraints at `erp/sample-postgres/init/01-ecommerce.sql:190-194`.
4. **Focused build passes** — superseded by the full integrated gate; model and tests passed within PASS 118.

### T26 — Order status history

1. **`history_id` unique and non-null** — `dw/snowflake/analytics/tests/test_stg_order_status_history.py:82-90` asserts the exact test set `{"not_null", "unique"}`; definition is at `dw/snowflake/analytics/models/silver/stg_order_status_history.yml:7-11`.
2. **Order references orders** — `dw/snowflake/analytics/tests/test_stg_order_status_history.py:92-114` asserts the relationship depends on `model.snowflake_analytics.stg_orders` and includes `not_null`; definition is at `dw/snowflake/analytics/models/silver/stg_order_status_history.yml:13-20`.
3. **Accepted status and UTC `changed_at`** — `dw/snowflake/analytics/tests/test_stg_order_status_history.py:116-127` asserts the exact source status list `["pending", "paid", "processing", "shipped", "delivered", "cancelled"]`, matching `erp/sample-postgres/init/01-ecommerce.sql:202-204`. `dw/snowflake/analytics/tests/test_stg_order_status_history.py:77-80` asserts `"convert_timezone('utc', changed_at) as changed_at_utc"`.
4. **Focused build passes** — superseded by the full integrated gate; model and tests passed within PASS 118.

### T27 — Payments

1. **`payment_id` unique and non-null** — `dw/snowflake/analytics/tests/test_stg_payments.py:82-96` asserts the exact test set `{"not_null", "unique"}`; definition is at `dw/snowflake/analytics/models/silver/stg_payments.yml:7-11`.
2. **Order references orders** — `dw/snowflake/analytics/tests/test_stg_payments.py:97-106` asserts the relationship depends on `model.snowflake_analytics.stg_orders`; requiredness is declared at `dw/snowflake/analytics/models/silver/stg_payments.yml:13-20` and passed in the integrated gate.
3. **Exact source status and provider domains** — `dw/snowflake/analytics/tests/test_stg_payments.py:108-132` asserts provider `["card", "paypal", "bank_transfer"]` and status `["pending", "authorized", "captured", "failed", "refunded"]`, matching `erp/sample-postgres/init/01-ecommerce.sql:215-219`.
4. **Non-negative amount and required currency** — `dw/snowflake/analytics/tests/test_stg_payments.py:133-140` asserts `currency` includes `not_null`; `dw/snowflake/analytics/tests/test_stg_payments.py:142-149` asserts `"where amount < 0"`. The rejection predicate is `dw/snowflake/analytics/tests/assert_stg_payments_amount_nonnegative.sql:3`: `where amount < 0`, matching `erp/sample-postgres/init/01-ecommerce.sql:213-214`.
5. **Focused build passes** — superseded by the full integrated gate; model and tests passed within PASS 118.

### T28 — Shipments

1. **`shipment_id` unique and non-null** — `dw/snowflake/analytics/tests/test_stg_shipments.py:84-98` asserts the exact set `{"not_null", "unique"}`; definition is at `dw/snowflake/analytics/models/silver/stg_shipments.yml:7-11`.
2. **Order and carrier references valid** — `dw/snowflake/analytics/tests/test_stg_shipments.py:99-109` asserts exact parents `stg_orders` and `stg_carriers`; both keys also have `not_null` at `dw/snowflake/analytics/models/silver/stg_shipments.yml:13-29`.
3. **Delivery never precedes shipment when both exist** — `dw/snowflake/analytics/tests/test_stg_shipments.py:111-121` asserts all three required clauses. The executed predicate is `dw/snowflake/analytics/tests/assert_stg_shipments_chronology.sql:3-5`: `delivered_at_utc is not null and shipped_at_utc is not null and delivered_at_utc < shipped_at_utc`, exactly matching `erp/sample-postgres/init/01-ecommerce.sql:232`.
4. **Focused build passes** — superseded by the full integrated gate; model and tests passed within PASS 118.

### T29 — Inventory movements

1. **`movement_id` unique and non-null** — `dw/snowflake/analytics/tests/test_stg_inventory_movements.py:82-96` asserts the exact set `{"not_null", "unique"}`; definition is at `dw/snowflake/analytics/models/silver/stg_inventory_movements.yml:7-11`.
2. **Required variant and optional order relationships** — `dw/snowflake/analytics/tests/test_stg_inventory_movements.py:97-114` asserts exact parents and the nullability outcome: `variant_id` has `not_null`, while `order_id` does not. Definitions are at `dw/snowflake/analytics/models/silver/stg_inventory_movements.yml:13-20` and `:36-43`.
3. **Non-zero delta and exact reason domain** — `dw/snowflake/analytics/tests/test_stg_inventory_movements.py:116-137` asserts reason `["restock", "sale", "return", "adjustment"]` and `"where quantity_delta = 0"`. The rejection predicate is `dw/snowflake/analytics/tests/assert_stg_inventory_movements_delta_nonzero.sql:3`: `where quantity_delta = 0`, matching `erp/sample-postgres/init/01-ecommerce.sql:242-244`.
4. **Complete Silver build has 16 views** — `dw/snowflake/analytics/tests/test_stg_inventory_movements.py:140-151` asserts `len(silver_views) == 16`; the integrated gate found and successfully created 16 view models.

## Spec-Anchored Silver Acceptance Criteria

| Silver AC | Scope-qualified outcome | Evidence | Result |
| --- | --- | --- | --- |
| AC1 | Seven new source-conformed views complete the 16-view Silver layer | `dw/snowflake/analytics/tests/test_stg_inventory_movements.py:140-151` — `self.assertEqual(len(silver_views), 16)`; integrated gate created 16 views | PASS |
| AC4 | Natural keys, source grain, nullability, domains, and passthrough semantics are preserved | Grain/key/domain assertions cited above; each model selects only its corresponding source, for example `dw/snowflake/analytics/models/silver/stg_orders.sql:1-20` and `stg_order_items.sql:1-10` | PASS |
| AC5 | Every timestamp in T23–T29 is converted to UTC and suffixed `_at_utc` | Exact `assertIn("convert_timezone('utc', ...) as ..._utc", raw_code)` assertions at cart items `:77-82`, orders `:77-82`, history `:77-80`, payments `:77-80`, shipments `:77-82`, and inventory movements `:77-80`; T25 has no timestamp | PASS |
| AC6 | All primary keys are non-null and unique, including composite source grains | Exact generic-test sets and singular rejection predicates cited in each task section | PASS |
| AC7 | Every relevant foreign key uses the exact Silver parent; optionality is preserved | Exact relationship dependency assertions cited for all seven models | PASS |
| AC8 | Order and payment statuses match the source domains exactly | Orders `test_stg_orders.py:127-138`; history `test_stg_order_status_history.py:116-127`; payments `test_stg_payments.py:108-132` | PASS |
| AC9 | Critical Silver test failures produce a failing gate and cannot be silently warned | `dw/snowflake/analytics/dbt_project.yml:9-12` has `warn_error_options.error: all`; all seven discrimination runs exited 1 on violated contracts. Gold completion ordering remains outside this interim scope because T30–T42 are pending | PASS (scope-qualified) |

The exact status/provider/reason outcomes match the PostgreSQL source DDL. No spec-precision gaps were found in T23–T29.

## Design and Scope Inspection

- All seven models are configured as views by `dw/snowflake/analytics/dbt_project.yml:29-35`.
- Each model contains one direct `source('ecommerce', '<table>')` dependency and no `ref()`, join, aggregation, business metric, or branching logic.
- Select lists preserve source business columns and only rename timestamp projections after `convert_timezone('UTC', ...)`.
- Composite grains remain composite; no synthetic keys or deduplication alter source semantics.
- No business metrics or cross-entity joins were introduced.
- `git diff --check 6ca337d..1ce5e8a` passed.
- The diff is limited to task/spec progress plus the seven models, seven YAML contracts, eight singular SQL tests, and seven static contract test files expected for T23–T29.

## Edge Cases

- Zero quantity in cart/order items is rejected (`qty <= 0`).
- Negative financial values are rejected; zero remains allowed where the source allows it.
- Discounts below 0 or above 1 are rejected.
- Shipment chronology is only compared when both timestamps exist, preserving source null semantics.
- Inventory deltas may be positive or negative but never zero.
- Optional inventory-movement `order_id` remains nullable while still relationship-tested when populated.
- Closed order, payment, provider, and movement-reason domains are asserted exactly.
- Empty Bronze inputs create empty views and do not fabricate rows because every model is a projection over one source.

## Gate Results

### Integrated dbt gate

- **Command**: `C:\venvs\delab\Scripts\dbt.exe build --project-dir dw\snowflake\analytics --profiles-dir dw\snowflake\analytics`
- **Result**: PASS
- **Models**: 16/16 view models passed
- **Data tests**: 102/102 passed
- **Total**: PASS=118, WARN=0, ERROR=0, SKIP=0, TOTAL=118
- **Warning policy**: project-level `warn_error_options.error: all` was active; no incompatible `--warn-error` flag was passed.

### Static contract gate

- **Command**: `PYTHONDONTWRITEBYTECODE=1 C:\venvs\delab\Scripts\python.exe -m unittest discover -s dw\snowflake\analytics\tests -p "test_stg_*.py"`
- **Result**: 60/60 passed, including 24/24 test methods in the seven T23–T29 files.

### Test integrity

- At `6ca337d`: 9 models and 55 data tests.
- At `1ce5e8a`: 16 models and 102 data tests.
- Delta: +7 models and +47 data tests; no tests were removed or weakened in the range.

## Discrimination Sensor

The sensor used detached temporary git worktree `1ce5e8a`; no mutation touched the real worktree. Each relevant Python contract file was run with `C:\venvs\delab\Scripts\python.exe` and `PYTHONDONTWRITEBYTECODE=1`.

| # | Task/outcome | Scratch mutation | Killing assertion | Result |
| --- | --- | --- | --- | --- |
| 1 | T23 UTC normalization | `convert_timezone('UTC', created_at)` → raw `created_at` | `test_stg_cart_items.py:77-82` exact timestamp expression | KILLED, exit 1 |
| 2 | T24 order status domain | Added `invalid` to accepted values | `test_stg_orders.py:127-138` exact list equality | KILLED, exit 1 |
| 3 | T25 positive quantity | `qty <= 0` → `qty < 0` | `test_stg_order_items.py:125-132` exact predicate membership | KILLED, exit 1 |
| 4 | T26 history UTC normalization | Replaced conversion with raw `changed_at` | `test_stg_order_status_history.py:77-80` exact timestamp expression | KILLED, exit 1 |
| 5 | T27 refunded payment semantics | Removed `refunded` from accepted values | `test_stg_payments.py:120-132` exact list equality | KILLED, exit 1 |
| 6 | T28 shipment chronology | `<` → `>` in rejection predicate | `test_stg_shipments.py:111-121` exact predicate membership | KILLED, exit 1 |
| 7 | T29 adjustment movement semantics | Removed `adjustment` from accepted values | `test_stg_inventory_movements.py:116-128` exact list equality | KILLED, exit 1 |

**Sensor depth**: expanded data-integrity/payment run  
**Result**: 7 injected, 7 killed, 0 survived — PASS.

Isolation note: the session initially observed the user-owned staged `.gitignore` addition for `.venv/`. Before sensor execution, that exact change was independently committed as `24d09b1`; the verifier did not create that commit. The `.venv/` content remained unchanged. The operative real-tree baseline at sensor time was clean, the scratch worktree was removed and pruned, and the real tree remained clean before this report was added. No sensor mutation leaked into the real tree.

## Code Quality

| Check | Result |
| --- | --- |
| Minimum source-conformed projections | PASS |
| Surgical T23–T29 scope | PASS |
| No joins or business metrics | PASS |
| Exact source domains and boundary predicates | PASS |
| Natural/composite grains preserved | PASS |
| UTC naming and conversion convention | PASS |
| Tests map to Done-when criteria and Silver ACs | PASS |
| No unclaimed scoped tests | PASS |
| Guidelines followed: `design.md:141-153`, `dbt_project.yml:9-12,29-35` | PASS |

## Summary

**Overall**: PASS for interim delivery group T23–T29.

- **Done-when**: 30/30
- **Spec-anchored Silver ACs**: 7/7 applicable, 0 precision gaps
- **Integrated gate**: 118/118
- **Static contracts**: 60/60
- **Sensor**: 7/7 killed, 0 survived
- **Ranked gaps**: none within T23–T29
- **Deferred**: deterministic full-feature completion validation and T30–T42 verification
