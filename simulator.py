def simulate_price_change(elasticity: float, pct_price_change: float, current_units: float, current_price: float):
    """
    elasticity: the category's price elasticity coefficient (negative number)
    pct_price_change: proposed % change in price, e.g. -15 for a 15% discount
    current_units: current average weekly units sold
    current_price: current average price

    Returns a dict with predicted volume change, new volume, and
    estimated revenue impact.
    """
    # % change in volume = elasticity * % change in price
    pct_volume_change = elasticity * pct_price_change

    new_units = current_units * (1 + pct_volume_change / 100)
    new_price = current_price * (1 + pct_price_change / 100)

    current_revenue = current_units * current_price
    new_revenue = new_units * new_price
    pct_revenue_change = (new_revenue - current_revenue) / current_revenue * 100

    return {
        "pct_volume_change": round(pct_volume_change, 2),
        "predicted_units": round(new_units, 1),
        "predicted_price": round(new_price, 2),
        "current_revenue": round(current_revenue, 2),
        "predicted_revenue": round(new_revenue, 2),
        "pct_revenue_change": round(pct_revenue_change, 2),
    }


if __name__ == "__main__":
    # quick manual test
    example = simulate_price_change(
        elasticity=-1.8,
        pct_price_change=-15,
        current_units=500,
        current_price=3.00,
    )
    print(example)
