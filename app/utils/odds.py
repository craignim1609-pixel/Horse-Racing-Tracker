from functools import reduce


# ---------------------------------------------------------
# FRACTIONAL → DECIMAL
# ---------------------------------------------------------
def fractional_to_decimal(frac: str) -> float:
    """
    Converts fractional odds (e.g. '5/2') to decimal odds.
    Example: 5/2 → 3.5
    """
    try:
        num, den = map(int, frac.split("/"))
        return num / den + 1
    except Exception:
        return 1.0  # safe fallback


# ---------------------------------------------------------
# PLACE ODDS (e.g. 1/5, 1/4, 1/6)
# ---------------------------------------------------------
def place_decimal(frac: str, place_fraction: float = 0.2) -> float:
    """
    Converts fractional odds to place odds.
    place_fraction = 0.2 → 1/5 odds
    """
    try:
        num, den = map(int, frac.split("/"))
        return (num * place_fraction) / den + 1
    except Exception:
        return 1.0


# ---------------------------------------------------------
# ACCUMULATOR DECIMAL
# ---------------------------------------------------------
def accumulator_decimal(odds_list: list[float]) -> float:
    """
    Multiplies decimal odds together for accumulator returns.
    """
    if not odds_list:
        return 0.0
    return reduce(lambda a, b: a * b, odds_list)


# ---------------------------------------------------------
# EACH-WAY RETURN (2.50 EW example)
# ---------------------------------------------------------
def ew_250_return(win_decimal: float, place_decimal_val: float) -> float:
    """
    Calculates EW return for a £2.50 each-way bet (£5 total stake).
    """
    stake_each = 2.50
    win_return = stake_each * win_decimal
    place_return = stake_each * place_decimal_val
    return round(win_return + place_return, 2)
