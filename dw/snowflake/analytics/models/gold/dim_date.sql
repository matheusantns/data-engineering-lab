with order_dates as (
    select distinct
        cast(ordered_at_utc as date) as full_date
    from {{ ref('stg_orders') }}
    where ordered_at_utc is not null
)

select
    to_number(to_char(full_date, 'YYYYMMDD')) as date_key,
    full_date,
    day(full_date) as day_of_month,
    dayofweekiso(full_date) as day_of_week,
    weekiso(full_date) as week_of_year,
    month(full_date) as month_number,
    trim(to_char(full_date, 'MMMM')) as month_name,
    quarter(full_date) as quarter_number,
    year(full_date) as year_number
from order_dates
