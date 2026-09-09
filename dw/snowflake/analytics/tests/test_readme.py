import re
import unittest
from pathlib import Path


README_PATH = Path(__file__).resolve().parents[2] / "README.md"

SILVER_MODELS = {
    "stg_users",
    "stg_addresses",
    "stg_categories",
    "stg_products",
    "stg_product_variants",
    "stg_product_images",
    "stg_inventory",
    "stg_carriers",
    "stg_carts",
    "stg_cart_items",
    "stg_orders",
    "stg_order_items",
    "stg_order_status_history",
    "stg_payments",
    "stg_shipments",
    "stg_inventory_movements",
}

GOLD_MODELS = {
    "dim_date",
    "dim_customer",
    "dim_product",
    "fct_orders",
    "fct_order_items",
}

METRIC_ROWS = {
    (
        "Receita reconhecida",
        "`sum(fct_orders.recognized_revenue)`",
        "Moeda e período UTC",
    ),
    (
        "Pedidos pagos",
        "`count(*)` de pedidos com `recognized_revenue > 0`",
        "Moeda e período UTC",
    ),
    (
        "Ticket médio",
        "Receita reconhecida dividida por pedidos pagos",
        "Moeda e período UTC",
    ),
    (
        "Unidades vendidas",
        "`sum(fct_order_items.qty)` de pedidos com captura",
        "Período UTC",
    ),
    (
        "Receita de mercadorias",
        "`sum(fct_order_items.line_total)` de pedidos com captura",
        "Moeda e período UTC",
    ),
}


def section(markdown, heading):
    match = re.search(
        rf"^## {re.escape(heading)}\s*$([\s\S]*?)(?=^## |\Z)",
        markdown,
        flags=re.MULTILINE,
    )
    return match.group(1) if match else ""


class SnowflakeReadmeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readme = README_PATH.read_text(encoding="utf-8")

    def test_links_to_operational_entry_points(self):
        self.assertIn("[Bootstrap](bootstrap/)", self.readme)
        self.assertIn("[Projeto dbt](analytics/)", self.readme)
        self.assertIn("[Runbook](RUNBOOK.md)", self.readme)

    def test_documents_layered_dag_and_schemas(self):
        self.assertIn("PostgreSQL --> Bronze", self.readme)
        self.assertIn("Bronze --> Silver", self.readme)
        self.assertIn("Silver --> Gold", self.readme)
        self.assertIn("`DATA_LAB.BRONZE`", self.readme)
        self.assertIn("`DATA_LAB.SILVER`", self.readme)
        self.assertIn("`DATA_LAB.GOLD`", self.readme)

    def test_lists_exactly_sixteen_silver_models(self):
        model_names = set(re.findall(r"`(stg_[a-z_]+)`", section(self.readme, "Silver")))
        self.assertEqual(model_names, SILVER_MODELS)

    def test_lists_exactly_five_gold_models(self):
        model_names = set(
            re.findall(
                r"`((?:dim|fct)_[a-z_]+)`",
                section(self.readme, "Gold"),
            )
        )
        self.assertEqual(model_names, GOLD_MODELS)

    def test_defines_five_metrics_and_their_grains(self):
        metrics_section = section(self.readme, "Métricas")
        rows = {
            tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
            for line in metrics_section.splitlines()
            if line.startswith("|") and "---" not in line and "Métrica" not in line
        }
        self.assertEqual(rows, METRIC_ROWS)


if __name__ == "__main__":
    unittest.main()
