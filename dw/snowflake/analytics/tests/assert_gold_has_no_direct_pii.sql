with gold_columns as (
    select
        table_name,
        column_name,
        lower(column_name) as normalized_column_name
    from {{ ref('dim_customer').database }}.information_schema.columns
    where upper(table_schema) = upper(
        '{{ ref('dim_customer').schema }}'
    )
),

classified_columns as (
    select
        table_name,
        column_name,
        case
            when (
                normalized_column_name = 'username'
                or regexp_like(
                    normalized_column_name,
                    '(^|_)name($|_)'
                )
            )
            and normalized_column_name not in (
                'product_name',
                'variant_name',
                'category_name',
                'month_name'
            ) then 'name'
            when regexp_like(
                normalized_column_name,
                '(^|_)(email|e_mail)($|_)'
            ) then 'email'
            when regexp_like(
                normalized_column_name,
                '(^|_)(phone|telephone|mobile)($|_)'
            ) then 'phone'
            when regexp_like(
                normalized_column_name,
                '(^|_)(address|street|postal_code|zip_code)($|_)'
            ) then 'address'
            when regexp_like(
                normalized_column_name,
                '(^|_)password_hash($|_)'
            ) then 'password_hash'
        end as pii_type
    from gold_columns
)

select
    table_name,
    column_name,
    pii_type
from classified_columns
where pii_type is not null
order by table_name, column_name
