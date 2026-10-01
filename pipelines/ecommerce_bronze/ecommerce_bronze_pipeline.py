import dlt
import sqlalchemy as sa
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


def exclude_sensitive_columns(table: sa.Table) -> sa.Table:
    if table.name == "users" and "password_hash" in table.c:
        table._columns.remove(table.c.password_hash)
    return table


def load_ecommerce_bronze() -> None:
    source = sql_database(
        schema="public",
        table_names=TABLES,
        reflection_level="full",
        chunk_size=50_000,
        table_adapter_callback=exclude_sensitive_columns,
    )

    pipeline = dlt.pipeline(
        pipeline_name="ecommerce_bronze",
        destination="snowflake",
        dataset_name="bronze",
    )

    # drop_resources: write_disposition="replace" swaps data but does not remove
    # columns. Without a refresh, an old NOT NULL password_hash left in Snowflake
    # after exclude_sensitive_columns still receives NULL and fails COPY.
    load_info = pipeline.run(
        source,
        write_disposition="replace",
        refresh="drop_resources",
    )

    print(load_info)

if __name__ == "__main__":
    load_ecommerce_bronze()