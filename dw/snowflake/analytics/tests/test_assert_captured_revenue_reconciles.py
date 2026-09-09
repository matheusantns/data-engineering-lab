import sqlite3
import unittest
from pathlib import Path


TEST_SQL_PATH = Path(__file__).with_name(
    "assert_captured_revenue_reconciles.sql"
)


class AssertCapturedRevenueReconcilesTest(unittest.TestCase):
    def setUp(self):
        self.sql = TEST_SQL_PATH.read_text(encoding="utf-8")
        self.executable_sql = self.sql.replace(
            "{{ ref('fct_orders') }}",
            "fct_orders",
        ).replace(
            "{{ ref('stg_payments') }}",
            "stg_payments",
        )

    def run_reconciliation(self, orders, payments):
        with sqlite3.connect(":memory:") as connection:
            connection.execute(
                """
                create table fct_orders (
                    order_id integer,
                    currency text,
                    recognized_revenue decimal(12, 2)
                )
                """
            )
            connection.execute(
                """
                create table stg_payments (
                    payment_id integer,
                    order_id integer,
                    amount decimal(12, 2),
                    currency text,
                    status text
                )
                """
            )
            connection.executemany(
                "insert into fct_orders values (?, ?, ?)",
                orders,
            )
            connection.executemany(
                "insert into stg_payments values (?, ?, ?, ?, ?)",
                payments,
            )
            return connection.execute(self.executable_sql).fetchall()

    def test_valid_captured_revenue_by_currency_returns_no_rows(self):
        failures = self.run_reconciliation(
            orders=[
                (1, "USD", 100.00),
                (2, "USD", 40.00),
                (3, "EUR", 70.00),
            ],
            payments=[
                (1, 1, 100.00, "USD", "captured"),
                (2, 2, 40.00, "USD", "captured"),
                (3, 3, 70.00, "EUR", "captured"),
            ],
        )

        self.assertEqual(failures, [])

    def test_equal_overall_total_does_not_hide_currency_mismatches(self):
        failures = self.run_reconciliation(
            orders=[
                (1, "USD", 100.00),
                (2, "EUR", 70.00),
            ],
            payments=[
                (1, 1, 90.00, "USD", "captured"),
                (2, 2, 80.00, "EUR", "captured"),
            ],
        )

        self.assertEqual(failures, [("EUR",), ("USD",)])

    def test_non_captured_statuses_do_not_contribute_to_revenue(self):
        failures = self.run_reconciliation(
            orders=[(1, "USD", 100.00)],
            payments=[
                (1, 1, 100.00, "USD", "captured"),
                (2, 1, 20.00, "USD", "pending"),
                (3, 1, 30.00, "USD", "failed"),
                (4, 1, 40.00, "USD", "refunded"),
            ],
        )

        self.assertEqual(failures, [])

    def test_refunded_revenue_mutation_is_rejected(self):
        failures = self.run_reconciliation(
            orders=[(1, "USD", 140.00)],
            payments=[
                (1, 1, 100.00, "USD", "captured"),
                (2, 1, 40.00, "USD", "refunded"),
            ],
        )

        self.assertEqual(failures, [("USD",)])

    def test_empty_relations_return_no_rows(self):
        failures = self.run_reconciliation(orders=[], payments=[])

        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
