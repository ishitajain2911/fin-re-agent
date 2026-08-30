from anthropic import beta_tool

@beta_tool

def calculate_pe_ratio(price: float, eps: float) -> str:
    
    """
    Compute the price-to-earnings (P/E) ratio: High P/E (say 30+) → expensive; the market is pricing in strong future growth (or the stock is overvalued)
Low P/E (say under ~12) → cheap; the market is pessimistic (or it's undervalued, or a shrinking business)
It's only meaningful in comparison — to the company's own history, to sector peers, or to the market (the S&P 500 historically sits around 15–20).

    Args:
    price: the current market price of one share, in USD.        
    eps: earnings per share over the trailing twelve months (TTM) — the last four reported quarters added together — in USD per share."""

    if eps <= 0:
        return f"P/E ratio not meaningful — EPS is {eps}, i.e. zero or negative, so the company had no positive earnings this period." 
    ratio = price/eps
    return f" P/E ratio: {ratio: .2f}, from price : {price}, and eps: {eps}"

@beta_tool
def calculate_revenue_growth(current_revenue: float, prior_revenue: float) -> str:
    """ 
        Compute year-over-year (YoY) revenue growth as a percentage: the change in
    total revenue between the current period and the same period one year earlier.
    Positive means the business is growing, negative means it's shrinking, and the
    magnitude matters — mid-single-digit growth signals a mature/slow business,
    while 20%+ signals a high-growth company. Comparing the same period one year
    apart cancels out seasonality.

    Args:
        current_revenue: total revenue for the most recent period, in USD.
        prior_revenue: total revenue for the same period one year earlier — same
            units and same period type as current_revenue (quarter vs. quarter,
            or full-year vs. full-year).
    """
    if prior_revenue <=0:
        return f"Prior revenue not meaningful — prior revenue is {prior_revenue}, i.e. zero or negative so a growth percentage can't be computed / is meaningless.."
    percent_change = (current_revenue - prior_revenue) / prior_revenue * 100 
    return f"YoY revenue growth: : {percent_change:.2f}% from prior revenue:  {prior_revenue} and current revenue: {current_revenue}"


if __name__ == "__main__":
        result = calculate_pe_ratio(100, 5)
        assert "20.00" in result, result

        result_edge = calculate_pe_ratio(200,0)
        assert "not meaningful" in result_edge, result_edge

        revenue_growth = calculate_revenue_growth(400, 200)
        assert "100.00%" in revenue_growth, revenue_growth

        revenue_growth_edge = calculate_revenue_growth(100,0)
        assert "not meaningful" in revenue_growth_edge, revenue_growth_edge

        print("all asserts passed")