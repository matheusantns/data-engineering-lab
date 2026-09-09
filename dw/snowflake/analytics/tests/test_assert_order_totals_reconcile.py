import sqlite3
import unittest
from pathlib import Path


TEST_SQL_PATH = Path(__file__).with_name("assert_order_totals_reconcile.sql")


class AssertOrderTotalsReconcileTest(unittest.TestCase):
    def setUp(self):
        self.sql = TEST_SQL_PATH.read_text(encoding="utf-8")
        self.executable_sql = self.sql.replace(
            "{{ ref('fct_orders') }}",
            "fct_orders",
        )

    def run_reconciliation(self, rows):
        with sqlite3.connect(":memory:") as connection:
            connection.execute(
                """
                create table fct_orders (
                    order_id integer,
                    subtotal decimal(12, 2),
                    discount_total decimal(12, 2),
                    shipping_total decimal(12, 2),
                    grand_total decimal(12, 2)
                )
                """
            )
            connection.executemany(
                "insert into fct_orders values (?, ?, ?, ?, ?)",
                rows,
            )
            return connection.execute(self.executable_sql).fetchall()

    def test_valid_order_totals_return_no_rows(self):
        failures = self.run_reconciliation(
            [
                (1, 100.00, 10.00, 5.00, 95.00),
                (2, 50.25, 0.25, 0.00, 50.00),
            ]
        )

        self.assertEqual(failures, [])

    def test_empty_orders_return_no_rows(self):
        failures = self.run_reconciliation([])

        self.assertEqual(failures, [])

    def test_mutated_grand_total_is_rejected(self):
        failures = self.run_reconciliation(
            [
                (1, 100.00, 10.00, 5.00, 95.00),
                (2, 50.25, 0.25, 0.00, 50.01),
            ]
        )

        self.assertEqual(failures, [(2,)])

    def test_query_declares_money_precision_and_uses_gold_fact(self):
        normalized_sql = " ".join(self.sql.lower().split())

        self.assertIn("{{ ref('fct_orders') }}", self.sql)
        self.assertGreaterEqual(normalized_sql.count("decimal(12, 2)"), 2)


if __name__ == "__main__":
    unittest.main()
