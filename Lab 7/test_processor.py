import math

from hypothesis import given, settings, strategies as st
from processor import lookup_drink_code, calculate_average_shot_cost, parse_order_modifiers


# ---------------------------------------------------------------------------
# lookup_drink_code
# ---------------------------------------------------------------------------

@given(st.text() | st.none())
def test_lookup_drink_code_no_crash(s):
    try:
        result = lookup_drink_code(s)
    except Exception as e:
        assert False, f"lookup_drink_code crashed on {s!r} with: {type(e).__name__}: {e}"
    # Valid codes give a positive price, anything else gives None
    assert result is None or (isinstance(result, float) and result > 0)


@given(st.sampled_from(["LAT", "CAP", "ESP", "AME", "MOC"]), st.text())
def test_lookup_drink_code_valid_prefix_any_case(prefix, suffix):
    # Every menu prefix (any letter case, any trailing text) must be found
    code = "".join(c.lower() if i % 2 else c for i, c in enumerate(prefix)) + suffix
    try:
        result = lookup_drink_code(code)
    except Exception as e:
        assert False, f"lookup_drink_code crashed on valid code {code!r} with: {type(e).__name__}: {e}"
    assert result is not None, f"valid drink code {code!r} was not found"


# ---------------------------------------------------------------------------
# calculate_average_shot_cost
# ---------------------------------------------------------------------------

@given(st.text() | st.none())
def test_calculate_average_shot_cost_safe(s):
    try:
        result = calculate_average_shot_cost(s)
    except Exception as e:
        assert False, f"calculate_average_shot_cost crashed on {s!r} with: {type(e).__name__}: {e}"
    assert isinstance(result, float) and math.isfinite(result)


@given(st.lists(st.floats(allow_nan=True, allow_infinity=True), max_size=10))
def test_calculate_average_shot_cost_numeric_csv(values):
    # CSVs built from real numbers, including empty lists, NaN and infinity
    csv = ",".join(str(v) for v in values)
    try:
        result = calculate_average_shot_cost(csv)
    except Exception as e:
        assert False, f"calculate_average_shot_cost crashed on {csv!r} with: {type(e).__name__}: {e}"
    assert isinstance(result, float) and math.isfinite(result)


# ---------------------------------------------------------------------------
# parse_order_modifiers
# ---------------------------------------------------------------------------

@given(st.text() | st.none())
def test_parse_order_modifiers_safe(s):
    try:
        result = parse_order_modifiers(s)
    except Exception as e:
        assert False, f"parse_order_modifiers crashed on {s!r} with: {type(e).__name__}: {e}"
    assert isinstance(result, dict)


@settings(max_examples=200)
@given(st.lists(st.text(alphabet="ab:; ", max_size=6), max_size=5))
def test_parse_order_modifiers_separator_heavy(parts):
    # Inputs dense with ':' and ';' (missing colons, extra colons, empty items)
    spec = ";".join(parts)
    try:
        result = parse_order_modifiers(spec)
    except Exception as e:
        assert False, f"parse_order_modifiers crashed on {spec!r} with: {type(e).__name__}: {e}"
    assert isinstance(result, dict)
