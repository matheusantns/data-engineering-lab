import sqlite3
import unittest
from pathlib import Path


TEST_SQL_PATH = Path(__file__).with_name("assert_item_totals_reconcile.sql")


class AssertItemTotalsReconcileTest(unittest.TestCase):
    def setUp(self):
        self.sql = TEST_SQL_PATH.read_text(encoding="utf-8")
        self.executable_sql = self.sql.replace(
            "{{ ref('fct_order_items') }}",
            "fct_order_items",
        ).replace(
            "{{ ref('fct_orders') }}",
            "fct_orders",
        )

    def run_reconciliation(self, orders, items):
        with sqlite3.connect(":memory:") as connection:
            connection.execute(
                """
                create table fct_orders (
                    order_id integer,
                    subtotal decimal(12, 2),
                    discount_total decimal(12, 2)
                )
                """
            )
            connection.execute(
                """
                create table fct_order_items (
                    order_id integer,
                    line_total decimal(12, 2)
                )
                """
            )
            connection.executemany(
                "insert into fct_orders values (?, ?, ?)",
                orders,
            )
            connection.executemany(
                "insert into fct_order_items values (?, ?)",
                items,
            )
            return connection.execute(self.executable_sql).fetchall()

    def test_valid_item_totals_return_no_rows(self):
        failures = self.run_reconciliation(
            orders=[
                (1, 100.00, 10.00),
                (2, 50.00, 0.00),
            ],
            items=[
                (1, 30.00),
                (1, 60.00),
                (2, 20.00),
                (2, 29.99),
            ],
        )

        self.assertEqual(failures, [])

    def test_empty_orders_and_items_return_no_rows(self):
        failures = self.run_reconciliation(orders=[], items=[])

        self.assertEqual(failures, [])

    def test_line_total_mutation_above_tolerance_is_rejected(self):
        failures = self.run_reconciliation(
            orders=[
                (1, 100.00, 10.00),
                (2, 50.00, 0.00),
            ],
            items=[
                (1, 30.00),
                (1, 60.00),
                (2, 20.00),
                (2, 29.97),
            ],
        )

        self.assertEqual(failures, [(2,)])

    def test_query_documents_and_applies_one_cent_per_item_tolerance(self):
        normalized_sql = " ".join(self.sql.lower().split())

        self.assertIn("one cent per item", self.sql.lower())
        self.assertIn("0.01 * items.item_count", normalized_sql)
        self.assertIn("{{ ref('fct_order_items') }}", self.sql)
        self.assertIn("{{ ref('fct_orders') }}", self.sql)


if __name__ == "__main__":
    unittest.main()
