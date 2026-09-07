import dlt
from dlt.sources.sql_database import sql_database

TABLES = [
    "users",
    "addresses",
    "categories",
    "products",
    "product_variants",
    "product_images",
    "inventory",
    "carriers",
    "carts",
    "cart_items",
    "orders",
    "order_items",
    "order_status_history",
    "payments",
    "shipments",
    "inventory_movements",
]

def load_ecommerce_bronze() -> None:
    source = sql_database(
        schema="public",
        table_names=TABLES,
        reflection_level="full",
        chunk_size=50_000,
    )

    pipeline = dlt.pipeline(
        pipeline_name="ecommerce_bronze",
        destination="snowflake",
        dataset_name="bronze",
    )

    load_info = pipeline.run(
        source,
        write_disposition="replace",
    )

    print(load_info)

if __name__ == "__main__":
    load_ecommerce_bronze()