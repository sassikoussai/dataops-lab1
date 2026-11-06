select order_id, quantity
from {{ ref('orders_clean') }}
where quantity <= 0
