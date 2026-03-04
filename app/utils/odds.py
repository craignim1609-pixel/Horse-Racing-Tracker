def fractional_to_decimal(frac: str) -> float:
    num, den = map(int, frac.split('/'))
    return num / den + 1

def place_decimal(frac: str) -> float:
    num, den = map(int, frac.split('/'))
    return (num / 5) / den + 1
