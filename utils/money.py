MONEDA = "DOP"
MIN_PRODUCT_PRICE = 1.00


def money(amount, decimals=2, spaced=False):
    try:
        value = float(amount)
    except (TypeError, ValueError):
        value = 0.0
    gap = " " if spaced else ""
    return f"{MONEDA}${gap}{value:,.{decimals}f}"


def rich_money(amount, decimals=2, spaced=False, font_size=10):
    """
    Returns an HTML-formatted string where 'DOP' is slightly smaller and
    aligned at the top (superscript), followed by the dollar sign and amount.
    """
    try:
        value = float(amount)
    except (TypeError, ValueError):
        value = 0.0
    gap = "&nbsp;" if spaced else ""
    return f"<span style='font-size: {font_size}px; vertical-align: super;'>{MONEDA}</span>${gap}{value:,.{decimals}f}"


def max_discount_for_price(price):
    try:
        value = float(price)
    except (TypeError, ValueError):
        value = 0.0
    return max(0.0, value - float(MIN_PRODUCT_PRICE))
