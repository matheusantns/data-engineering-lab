import re
import sqlite3
import unittest
from pathlib import Path


TEST_SQL_PATH = Path(__file__).parent / "assert_gold_has_no_direct_pii.sql"


class AssertGoldHasNoDirectPiiTest(unittest.TestCase):
    def setUp(self):
        self.sql = TEST_SQL_PATH.read_text(encoding="utf-8")
        self.executable_sql = (
            self.sql.replace(
                "{{ ref('dim_customer').database }}.information_schema.columns",
                "information_schema_columns",
            )
            .replace("{{ ref('dim_customer').schema }}", "GOLD")
        )

    def run_validation(self, columns):
        with sqlite3.connect(":memory:") as connection:
            connection.create_function(
                "regexp_like",
                2,
                lambda value, pattern: int(
                    re.search(pattern, value or "") is not None
                ),
            )
            connection.execute(
                """
                create table information_schema_columns (
                    table_schema text,
                    table_name text,
                    column_name text
                )
                """
            )
            connection.executemany(
                "insert into information_schema_columns values (?, ?, ?)",
                columns,
            )
            return connection.execute(self.executable_sql).fetchall()

    def test_current_three_dimensions_and_two_facts_have_no_direct_pii(self):
        failures = self.run_validation(
            [
                ("GOLD", "DIM_DATE", "FULL_DATE"),
                ("GOLD", "DIM_CUSTOMER", "CUSTOMER_KEY"),
                ("GOLD", "DIM_PRODUCT", "PRODUCT_NAME"),
                ("GOLD", "DIM_PRODUCT", "VARIANT_NAME"),
                ("GOLD", "DIM_PRODUCT", "CATEGORY_NAME"),
                ("GOLD", "FCT_ORDERS", "ORDER_NUMBER"),
                ("GOLD", "FCT_ORDER_ITEMS", "PRODUCT_KEY"),
            ]
        )

        self.assertEqual(failures, [])

    def test_direct_pii_column_mutations_are_rejected(self):
        failures = self.run_validation(
            [
                ("GOLD", "DIM_CUSTOMER", "FULL_NAME"),
                ("GOLD", "DIM_CUSTOMER", "CUSTOMER_EMAIL"),
                ("GOLD", "DIM_CUSTOMER", "PHONE_NUMBER"),
                ("GOLD", "DIM_CUSTOMER", "STREET_ADDRESS"),
                ("GOLD", "DIM_CUSTOMER", "PASSWORD_HASH"),
            ]
        )

        self.assertEqual(
            failures,
            [
                ("DIM_CUSTOMER", "CUSTOMER_EMAIL", "email"),
                ("DIM_CUSTOMER", "FULL_NAME", "name"),
                ("DIM_CUSTOMER", "PASSWORD_HASH", "password_hash"),
                ("DIM_CUSTOMER", "PHONE_NUMBER", "phone"),
                ("DIM_CUSTOMER", "STREET_ADDRESS", "address"),
            ],
        )

    def test_direct_pii_outside_gold_is_not_reported(self):
        failures = self.run_validation(
            [
                ("SILVER", "STG_USERS", "EMAIL"),
                ("SILVER", "STG_USERS", "PHONE"),
                ("BRONZE", "USERS", "PASSWORD_HASH"),
            ]
        )

        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
