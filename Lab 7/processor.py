import math

MENU_PRICES = {
    "LAT": 4.50,
    "CAP": 4.00,
    "ESP": 3.00,
    "AME": 3.50,
    "MOC": 5.00,  # FIX: was "MOc", which could never match an upper-cased code
}


def lookup_drink_code(code_string):
    """Return the base price for a drink code, or None if the code is invalid."""
    # FIX: reject None / non-string input instead of crashing on .upper()
    if not isinstance(code_string, str):
        return None
    code_prefix = code_string.strip().upper()[:3]
    # FIX: .get() instead of [] so unknown codes return None, not KeyError
    return MENU_PRICES.get(code_prefix)


def calculate_average_shot_cost(pricing_csv):
    """Return the average of the valid prices in a CSV string (0.0 if none)."""
    # FIX: reject None / non-string input instead of crashing on .split()
    if not isinstance(pricing_csv, str):
        return 0.0
    prices = []
    for part in pricing_csv.split(','):
        part = part.strip()
        if not part:
            continue  # FIX: skip empty entries such as "1.0,,2.0" or ""
        try:
            value = float(part)
        except ValueError:
            continue  # FIX: skip non-numeric entries such as "abc"
        if not math.isfinite(value) or value < 0:
            continue  # FIX: skip nan / inf / negative prices
        prices.append(value)
    # FIX: no valid prices -> 0.0 instead of ZeroDivisionError
    if not prices:
        return 0.0
    # FIX: divide each price first so huge values cannot overflow the sum to inf
    return sum(p / len(prices) for p in prices)


def parse_order_modifiers(order_spec):
    """Parse 'key:value;key:value' into a dict, skipping malformed items."""
    modifier_dict = {}
    # FIX: reject None / non-string input instead of crashing on .split()
    if not isinstance(order_spec, str):
        return modifier_dict
    for item in order_spec.split(';'):
        # FIX: skip items with no ':' instead of crashing on unpacking
        if ':' not in item:
            continue
        # FIX: split only on the first ':' so "a:b:c" doesn't crash
        key, value = item.split(':', 1)
        key = key.strip()
        if not key:
            continue  # FIX: skip items with an empty key such as ":oat"
        modifier_dict[key] = value.strip()
    return modifier_dict


def main():
    print("==== Running lookup_drink_code ====")
    drink_input = input("Enter drink code prefix (e.g. LAT, CAP, ESP): ")
    price = lookup_drink_code(drink_input)
    if price is None:
        print("Invalid drink code:", repr(drink_input))
    else:
        print("Base Price: $", price)

    print("\n==== Running calculate_average_shot_cost ====")
    shots_input = input("Enter CSV of shot prices (e.g. 1.0, 1.5, 2.0): ")
    avg_price = calculate_average_shot_cost(shots_input)
    print("Average Shot Price: $", avg_price)

    print("\n==== Running parse_order_modifiers ====")
    spec_input = input("Enter modifiers (e.g. milk:oat;syrup:vanilla): ")
    mods = parse_order_modifiers(spec_input)
    print("Parsed Modifiers:", mods)


if __name__ == "__main__":
    main()
