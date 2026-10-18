"""Pure calculation functions. No I/O. All money in copper."""
from math import exp, log

CUT_FACTION = 0.05
CUT_NEUTRAL = 0.15


def net_profit(sale_price: int, cost: int, cut: float = CUT_FACTION, deposit: int = 0) -> float:
    """Sale minus cost, minus AH cut and deposit. Deposit is passed in: not modelled here."""
    return sale_price * (1 - cut) - cost - deposit


def vendor_floor_profit(listing_price: int, vendor_price: int, qty: int = 1) -> int:
    """Buy at auction, sell to vendor. Vendors take no cut. Positive = risk-free profit."""
    return vendor_price * qty - listing_price * qty


def inflation_index(prices_now: dict[int, float], prices_base: dict[int, float]) -> float:
    """Geometric mean of price ratios over the items present in both baskets. Base = 1.0."""
    ratios = [prices_now[i] / prices_base[i] for i in prices_now
              if i in prices_base and prices_base[i] > 0 and prices_now[i] > 0]
    if not ratios:
        raise ValueError("no overlapping priced items in basket")
    return exp(sum(log(r) for r in ratios) / len(ratios))


def real_discount(listing: float, ref_median: float, index_ref: float, index_now: float) -> float:
    """How far a listing sits below its reference median after adjusting that median to today's
    price level. 0.25 = 25% under real market value. Negative = above."""
    adjusted = ref_median * (index_now / index_ref)
    return 1 - listing / adjusted


# Initial thresholds are guesses to be tuned against predicted-vs-actual results.
def reliability(auctions: int | None, history_days: float, quantity: int | None,
                has_sales_estimate: bool, volatility: float | None) -> str:
    """Low / Medium / High from five inputs. volatility = (p75-p25)/median, lower is steadier."""
    pts = 0
    pts += 2 if (auctions or 0) >= 30 else 1 if (auctions or 0) >= 10 else 0
    pts += 2 if history_days >= 14 else 1 if history_days >= 3 else 0
    pts += 1 if (quantity or 0) >= 20 else 0
    pts += 1 if has_sales_estimate else 0
    if volatility is not None:
        pts += 1 if volatility <= 0.5 else 0
    return "High" if pts >= 6 else "Medium" if pts >= 3 else "Low"
