with currency_records as (
    select
        'fct_orders' as source_relation,
        cast(order_id as varchar) as record_id,
        currency
    from {{ ref('fct_orders') }}

    union all

    select
        'fct_order_items' as source_relation,
        cast(order_id as varchar) as record_id,
        currency
    from {{ ref('fct_order_items') }}

    union all

    select
        'stg_payments' as source_relation,
        cast(payment_id as varchar) as record_id,
        currency
    from {{ ref('stg_payments') }}
),

invalid_codes as (
    select
        'invalid_currency_code' as violation,
        source_relation,
        record_id,
        currency
    from currency_records
    where currency is null
        or not regexp_like(currency, '^[A-Z]{3}$')
),

item_currency_mismatches as (
    select
        'item_order_currency_mismatch' as violation,
        'fct_order_items' as source_relation,
        cast(items.order_id as varchar) as record_id,
        items.currency
    from {{ ref('fct_order_items') }} as items
    inner join {{ ref('fct_orders') }} as orders
        on items.order_id = orders.order_id
    where items.currency <> orders.currency
),

payment_currency_mismatches as (
    select
        'payment_order_currency_mismatch' as violation,
        'stg_payments' as source_relation,
        cast(payments.payment_id as varchar) as record_id,
        payments.currency
    from {{ ref('stg_payments') }} as payments
    inner join {{ ref('fct_orders') }} as orders
        on payments.order_id = orders.order_id
    where payments.currency <> orders.currency
)

select * from invalid_codes
union all
select * from item_currency_mismatches
union all
select * from payment_currency_mismatches
