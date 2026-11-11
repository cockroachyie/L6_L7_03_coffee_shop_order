"""
Lab 6 - Code (Line) Coverage test cases
SRN: PES1UG24CS248
Module under test: coffee_shop_order.py

Goal: execute every line of coffee_shop_order.py at least once.
(Branch coverage is handled in BranchCoverageTest_PES1UG24CS248_application.py)
"""
import pytest
from coffee_shop_order import process_order_batch, check_espresso_machine


# ---------------------------------------------------------------------------
# process_order_batch
# ---------------------------------------------------------------------------

# Starter test case (given)
def test_single_medium_coffee():
    orders = [
        {
            "paid": True,
            "size": "medium",
            "strict_allergy": False,
            "is_member": False,
            "customizations": [{"type": "standard", "cost": 0.5}]
        }
    ]
    result = process_order_batch(orders, 0.1)
    assert result["total"] == 5.5
    assert result["status"] == "COMPLETED"


# Line 3: raise ValueError
def test_invalid_orders_raises():
    with pytest.raises(ValueError):
        process_order_batch("not a list", 0.1)


# Line 10: unpaid order -> continue ; Line 54: NO_SALE
def test_unpaid_order_no_sale():
    orders = [{"paid": False, "size": "large"}]
    assert process_order_batch(orders, 0.1) == {"total": 0.0, "status": "NO_SALE"}


# Line 14: small size ; Line 40: syrup (capped)
def test_small_with_syrup():
    orders = [{"paid": True, "size": "small",
               "customizations": [{"type": "syrup", "cost": 3.0}]}]
    assert process_order_batch(orders, 0.0) == {"total": 4.5, "status": "COMPLETED"}


# Line 18: large size ; Line 45: member discount
def test_large_member_discount():
    orders = [{"paid": True, "size": "large", "is_member": True}]
    assert process_order_batch(orders, 0.0) == {"total": 5.4, "status": "COMPLETED"}


# Lines 35-38: allergen alert with strict allergy -> item zeroed, break
def test_strict_allergen_zeroes_item():
    orders = [{"paid": True, "size": "medium", "strict_allergy": True,
               "customizations": [{"type": "allergen_alert", "cost": 0.0}]}]
    assert process_order_batch(orders, 0.1) == {"total": 0.0, "status": "NO_SALE"}


# Lines 20-21: invalid size ; Lines 31-32: negative cost ; Line 52: AUDIT_REJECTED
def test_audit_rejected():
    orders = [
        {"paid": True, "size": "venti"},
        {"paid": True, "size": "small",
         "customizations": [{"type": "standard", "cost": -1.0}] * 4},
    ]
    assert process_order_batch(orders, 0.0) == {"total": 3.0, "status": "AUDIT_REJECTED"}


# ---------------------------------------------------------------------------
# check_espresso_machine
# ---------------------------------------------------------------------------

# Line 60: NO_DATA
def test_espresso_no_data():
    assert check_espresso_machine([]) == "NO_DATA"


# Line 68: SHUTDOWN (two consecutive temps > 96)
def test_espresso_shutdown():
    assert check_espresso_machine([[97.0, 98.0]]) == "SHUTDOWN"


# Line 70: streak reset ; Line 71: OPTIMAL
def test_espresso_optimal():
    assert check_espresso_machine([[90.0, 97.0, 92.0]]) == "OPTIMAL"
