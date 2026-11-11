import pytest
from coffee_shop_order import process_order_batch, check_espresso_machine


# ---------------------------------------------------------------------------
# process_order_batch
# ---------------------------------------------------------------------------

# Example test case (given):
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


# --- Input validation (line 2: both sides of the `or`) ---

def test_orders_not_a_list_raises():
    with pytest.raises(ValueError, match="Invalid orders list or tax rate"):
        process_order_batch({"paid": True}, 0.1)


def test_negative_tax_rate_raises():
    with pytest.raises(ValueError, match="Invalid orders list or tax rate"):
        process_order_batch([], -0.01)


def test_zero_tax_rate_is_valid():
    orders = [{"paid": True, "size": "small"}]
    result = process_order_batch(orders, 0)
    assert result == {"total": 3.0, "status": "COMPLETED"}


# --- Empty batch / unpaid orders ---

def test_empty_order_list_is_no_sale():
    assert process_order_batch([], 0.1) == {"total": 0.0, "status": "NO_SALE"}


def test_unpaid_order_is_skipped():
    orders = [{"paid": False, "size": "large"}]
    assert process_order_batch(orders, 0.1) == {"total": 0.0, "status": "NO_SALE"}


def test_missing_paid_key_defaults_to_unpaid():
    orders = [{"size": "large"}]
    assert process_order_batch(orders, 0.1) == {"total": 0.0, "status": "NO_SALE"}


def test_unpaid_order_skipped_but_paid_counted():
    orders = [{"paid": False, "size": "large"}, {"paid": True, "size": "small"}]
    result = process_order_batch(orders, 0.0)
    assert result == {"total": 3.0, "status": "COMPLETED"}


# --- Size pricing (every branch of the if/elif/else) ---

@pytest.mark.parametrize("size, expected", [
    ("small", 3.0),
    ("medium", 4.5),
    ("large", 6.0),
])
def test_size_base_prices(size, expected):
    orders = [{"paid": True, "size": size}]
    assert process_order_batch(orders, 0.0) == {"total": expected, "status": "COMPLETED"}


def test_missing_size_defaults_to_medium():
    orders = [{"paid": True}]
    assert process_order_batch(orders, 0.0) == {"total": 4.5, "status": "COMPLETED"}


def test_invalid_size_is_rejected():
    orders = [{"paid": True, "size": "venti"}]
    assert process_order_batch(orders, 0.1) == {"total": 0.0, "status": "NO_SALE"}


# --- Customizations ---

def test_negative_cost_customization_is_rejected_and_ignored():
    orders = [{"paid": True, "size": "small",
               "customizations": [{"type": "standard", "cost": -1.0}]}]
    assert process_order_batch(orders, 0.0) == {"total": 3.0, "status": "COMPLETED"}


def test_customization_missing_type_and_cost_uses_defaults():
    orders = [{"paid": True, "size": "small", "customizations": [{}]}]
    assert process_order_batch(orders, 0.0) == {"total": 3.0, "status": "COMPLETED"}


def test_syrup_under_cap_charged_in_full():
    orders = [{"paid": True, "size": "small",
               "customizations": [{"type": "syrup", "cost": 1.0}]}]
    assert process_order_batch(orders, 0.0)["total"] == 4.0


def test_syrup_exactly_at_cap():
    orders = [{"paid": True, "size": "small",
               "customizations": [{"type": "syrup", "cost": 1.5}]}]
    assert process_order_batch(orders, 0.0)["total"] == 4.5


def test_syrup_over_cap_is_capped_at_1_5():
    orders = [{"paid": True, "size": "small",
               "customizations": [{"type": "syrup", "cost": 3.0}]}]
    assert process_order_batch(orders, 0.0)["total"] == 4.5


def test_other_customization_charged_in_full():
    orders = [{"paid": True, "size": "small",
               "customizations": [{"type": "oat_milk", "cost": 2.0}]}]
    assert process_order_batch(orders, 0.0)["total"] == 5.0


# --- Allergen alerts ---

def test_allergen_alert_non_strict_keeps_price_and_continues():
    orders = [{"paid": True, "size": "small", "strict_allergy": False,
               "customizations": [
                   {"type": "allergen_alert", "cost": 0.0},
                   {"type": "syrup", "cost": 1.0},
               ]}]
    # alert counts as a rejection but the later syrup is still added
    assert process_order_batch(orders, 0.0) == {"total": 4.0, "status": "COMPLETED"}


def test_allergen_alert_strict_zeroes_item_and_stops():
    orders = [{"paid": True, "size": "large", "strict_allergy": True,
               "customizations": [
                   {"type": "syrup", "cost": 1.0},
                   {"type": "allergen_alert", "cost": 0.0},
                   {"type": "standard", "cost": 5.0},  # never reached (break)
               ]}]
    assert process_order_batch(orders, 0.1) == {"total": 0.0, "status": "NO_SALE"}


def test_strict_allergy_item_zeroed_other_items_still_billed():
    orders = [
        {"paid": True, "size": "large", "strict_allergy": True,
         "customizations": [{"type": "allergen_alert"}]},
        {"paid": True, "size": "small"},
    ]
    assert process_order_batch(orders, 0.0) == {"total": 3.0, "status": "COMPLETED"}


# --- Membership discount ---

def test_member_gets_ten_percent_discount():
    orders = [{"paid": True, "size": "large", "is_member": True}]
    assert process_order_batch(orders, 0.0) == {"total": 5.4, "status": "COMPLETED"}


def test_member_discount_then_tax():
    orders = [{"paid": True, "size": "medium", "is_member": True,
               "customizations": [{"type": "syrup", "cost": 0.5}]}]
    # (4.5 + 0.5) * 0.9 = 4.5 ; * 1.1 = 4.95
    assert process_order_batch(orders, 0.1) == {"total": 4.95, "status": "COMPLETED"}


# --- Audit threshold (rejected_items > 4) ---

def test_exactly_four_rejections_is_not_audited():
    orders = [{"paid": True, "size": "bad"} for _ in range(4)]
    orders.append({"paid": True, "size": "small"})
    assert process_order_batch(orders, 0.0) == {"total": 3.0, "status": "COMPLETED"}


def test_five_rejections_triggers_audit():
    orders = [{"paid": True, "size": "small",
               "customizations": [{"type": "x", "cost": -1.0}] * 5}]
    assert process_order_batch(orders, 0.1) == {"total": 3.3, "status": "AUDIT_REJECTED"}


def test_audit_takes_priority_over_no_sale():
    orders = [{"paid": True, "size": "bad"} for _ in range(5)]
    assert process_order_batch(orders, 0.1) == {"total": 0.0, "status": "AUDIT_REJECTED"}


def test_mixed_rejection_sources_counted_together():
    orders = [
        {"paid": True, "size": "huge"},                                   # 1
        {"paid": True, "size": "small",
         "customizations": [{"type": "allergen_alert"},                   # 2
                            {"type": "syrup", "cost": -0.5}]},           # 3
        {"paid": True, "size": "medium",
         "customizations": [{"type": "standard", "cost": -2.0},           # 4
                            {"type": "allergen_alert"}]},                 # 5
    ]
    result = process_order_batch(orders, 0.0)
    assert result == {"total": 7.5, "status": "AUDIT_REJECTED"}


# ---------------------------------------------------------------------------
# check_espresso_machine
# ---------------------------------------------------------------------------

def test_espresso_no_data_empty_list():
    assert check_espresso_machine([]) == "NO_DATA"


def test_espresso_no_data_none():
    assert check_espresso_machine(None) == "NO_DATA"


def test_espresso_all_normal_is_optimal():
    assert check_espresso_machine([[90.0, 92.5, 95.0], [93.0]]) == "OPTIMAL"


def test_espresso_empty_cycle_is_optimal():
    assert check_espresso_machine([[]]) == "OPTIMAL"


def test_espresso_exactly_96_is_not_overheat():
    assert check_espresso_machine([[96.0, 96.0, 96.0]]) == "OPTIMAL"


def test_espresso_single_spike_is_optimal():
    assert check_espresso_machine([[97.0, 90.0, 98.0]]) == "OPTIMAL"


def test_espresso_two_consecutive_overheats_shutdown():
    assert check_espresso_machine([[90.0, 97.0, 98.0, 90.0]]) == "SHUTDOWN"


def test_espresso_streak_resets_between_cycles():
    # 97 at end of cycle 1 and 97 at start of cycle 2 are NOT consecutive
    assert check_espresso_machine([[90.0, 97.0], [97.0, 90.0]]) == "OPTIMAL"


def test_espresso_shutdown_in_later_cycle():
    assert check_espresso_machine([[90.0, 91.0], [99.0, 100.0]]) == "SHUTDOWN"
