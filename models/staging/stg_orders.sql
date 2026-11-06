-- Staging: give each column its real type and repair what can be repaired.
-- No row is removed here.
select
    try_cast(src.order_id as integer)                                         as order_id,
    try_strptime(src.order_date, '%Y-%m-%d')::date                            as order_date,
    src.customer_id                                                           as customer_id,
    upper(left(trim(src.country), 1)) || lower(substr(trim(src.country), 2))  as country,
    src.product                                                               as product,
    try_cast(src.quantity as integer)                                         as quantity,
    try_cast(src.unit_price as decimal(10, 2))                                as unit_price,
    src._row_number                                                           as _row_number,
    src._loaded_at                                                            as _loaded_at
from {{ source('raw', 'orders') }} as src
