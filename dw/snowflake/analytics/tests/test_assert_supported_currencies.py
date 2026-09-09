import re
import sqlite3
import unittest
from pathlib import Path


TESTS_DIR = Path(__file__).parent
TEST_SQL_PATH = TESTS_DIR / "assert_supported_currencies.sql"
FCT_ORDERS_PATH = TESTS_DIR.parent / "models" / "gold" / "fct_orders.sql"
FCT_ORDER_ITEMS_PATH = (
    TESTS_DIR.parent / "models" / "gold" / "fct_order_items.sql"
)
REVENUE_RECONCILIATION_PATH = (
    TESTS_DIR / "assert_captured_revenue_reconciles.sql"
)


class AssertSupportedCurrenciesTest(unittest.TestCase):
    def setUp(self):
        self.sql = TEST_SQL_PATH.read_text(encoding="utf-8")
        self.executable_sql = (
            self.sql.replace("{{ ref('fct_orders') }}", "fct_orders")
            .replace(
                "{{ ref('fct_order_items') }}",
                "fct_order_items",
            )
            .replace("{{ ref('stg_payments') }}", "stg_payments")
        )

    def run_validation(self, orders, items, payments):
        with sqlite3.connect(":memory:") as connection:
            connection.create_function(
                "regexp_like",
                2,
                lambda value, pattern: (
                    0
                    if value is None
                    else int(re.fullmatch(pattern, value) is not None)
                ),
            )
            connection.execute(
                """
                create table fct_orders (
                    order_id integer,
                    currency text
                )
                """
            )
            connection.execute(
                """
                create table fct_order_items (
                    order_id integer,
                    product_key integer,
                    currency text
                )
                """
            )
            connection.execute(
                """
                create table stg_payments (
                    payment_id integer,
                    order_id integer,
                    currency text
                )
                """
            )
            connection.executemany(
                "insert into fct_orders values (?, ?)",
                orders,
            )
            connection.executemany(
                "insert into fct_order_items values (?, ?, ?)",
                items,
            )
            connection.executemany(
                "insert into stg_payments values (?, ?, ?)",
                payments,
            )
            return connection.execute(self.executable_sql).fetchall()

    def test_valid_usd_and_eur_remain_in_distinct_currency_groups(self):
        failures = self.run_validation(
            orders=[(1, "USD"), (2, "EUR")],
            items=[(1, 10, "USD"), (2, 20, "EUR")],
            payments=[(100, 1, "USD"), (200, 2, "EUR")],
        )

        self.assertEqual(failures, [])

    def test_null_and_non_iso_currency_codes_are_rejected(self):
        failures = self.run_validation(
            orders=[(1, None)],
            items=[(1, 10, "usd")],
            payments=[(100, 1, "EURO")],
        )

        self.assertEqual(
            failures,
            [
                ("invalid_currency_code", "fct_orders", "1", None),
                ("invalid_currency_code", "fct_order_items", "1", "usd"),
                ("invalid_currency_code", "stg_payments", "100", "EURO"),
            ],
        )

    def test_cross_currency_item_and_payment_mutations_are_rejected(self):
        failures = self.run_validation(
            orders=[(1, "USD"), (2, "EUR")],
            items=[(1, 10, "EUR"), (2, 20, "EUR")],
            payments=[(100, 1, "USD"), (200, 2, "USD")],
        )

        self.assertEqual(
            failures,
            [
                (
                    "item_order_currency_mismatch",
                    "fct_order_items",
                    "1",
                    "EUR",
                ),
                (
                    "payment_order_currency_mismatch",
                    "stg_payments",
                    "200",
                    "USD",
                ),
            ],
        )

    def test_financial_models_and_reconciliation_keep_currency_in_grain(self):
        orders_sql = FCT_ORDERS_PATH.read_text(encoding="utf-8").lower()
        items_sql = FCT_ORDER_ITEMS_PATH.read_text(encoding="utf-8").lower()
        reconciliation_sql = REVENUE_RECONCILIATION_PATH.read_text(
            encoding="utf-8"
        ).lower()

        self.assertIn("orders.currency", orders_sql)
        self.assertIn("orders.currency", items_sql)
        self.assertGreaterEqual(
            reconciliation_sql.count("group by currency"),
            2,
        )


if __name__ == "__main__":
    unittest.main()
