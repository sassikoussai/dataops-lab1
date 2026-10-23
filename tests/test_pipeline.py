import pandas as pd
import pytest

from pipeline.transform import clean_orders, revenue_by_country
from pipeline.validate import DataQualityError, check_schema


def make_orders(rows):
    """Build a small orders table. Each row only gives the columns it wants to change."""
    default = {
        "order_id": 1,
        "order_date": "2026-10-05",
        "customer_id": "C001",
        "country": "Tunisia",
        "product": "Mouse",
        "quantity": 1,
        "unit_price": 10.0,
    }
    return pd.DataFrame([{**default, **row} for row in rows])


def test_revenue_by_country():
    orders = make_orders(
        [
            {"order_id": 1, "country": "Tunisia", "quantity": 2, "unit_price": 10.0},
            {"order_id": 2, "country": "Tunisia", "quantity": 1, "unit_price": 5.0},
            {"order_id": 3, "country": "France", "quantity": 3, "unit_price": 1.0},
        ]
    )
    report = revenue_by_country(orders)
    assert report.set_index("country")["revenue"].to_dict() == {"France": 3.0, "Tunisia": 25.0}


def test_negative_quantity_is_rejected():
    orders = make_orders([{"order_id": 1, "quantity": -2}, {"order_id": 2, "quantity": 3}])
    clean, rejected = clean_orders(orders)
    assert list(clean["order_id"]) == [2]
    assert list(rejected["reject_reason"]) == ["invalid_quantity"]


def test_duplicate_order_is_rejected():
    orders = make_orders([
        {"order_id": 1, "quantity": 1},
        {"order_id": 1, "quantity": 2},
        {"order_id": 2, "quantity": 1},
    ])
    clean, rejected = clean_orders(orders)
    assert len(clean) == 2
    assert len(rejected) == 1
    assert list(rejected["reject_reason"]) == ["duplicate_order_id"]


def test_country_is_normalised():
    orders = make_orders([
        {"order_id": 1, "country": " france"},
        {"order_id": 2, "country": "FRANCE "},
    ])
    clean, rejected = clean_orders(orders)
    assert list(clean["country"]) == ["France", "France"]
    assert len(rejected) == 0


def test_check_schema_stops_on_missing_column():
    orders = make_orders([{"order_id": 1}])
    orders = orders.rename(columns={"unit_price": "price"})
    with pytest.raises(DataQualityError):
        check_schema(orders)

def test_unknown_country_is_rejected():
    orders = make_orders([{"order_id": 1, "country": "Spain"}, {"order_id": 2, "country": "Italy"}])
    clean, rejected = clean_orders(orders)
    assert list(clean["order_id"]) == [2]
    assert list(rejected["reject_reason"]) == ["unknown_country"]
