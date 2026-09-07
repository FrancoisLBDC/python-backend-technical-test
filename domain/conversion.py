from decimal import ROUND_HALF_UP, Decimal

_TWO_DECIMALS = Decimal("0.01")


def convert_amount(amount: Decimal, from_rate: Decimal, to_rate: Decimal) -> Decimal:
    """Convert an amount by triangulating through a shared reference rate.

    `from_rate` and `to_rate` are each currency's rate against that shared
    reference. Covers
    identity, reference -> X, X -> reference and X -> Y uniformly, since
    amount / from_rate * to_rate degrades correctly when either rate is 1.
    """
    result = amount / from_rate * to_rate
    return result.quantize(_TWO_DECIMALS, rounding=ROUND_HALF_UP)
