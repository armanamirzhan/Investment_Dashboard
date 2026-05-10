#!/usr/bin/env python3
"""
Fetch live market data for every public ticker in companies.json and update
data/financials.json + data/valuation_history.json. Re-runs the generators
unless --no-regen is passed.

Usage:
    python scripts/fetch_prices.py                # all public tickers, then regenerate
    python scripts/fetch_prices.py --no-regen     # fetch only
    python scripts/fetch_prices.py NVDA MSFT      # specific tickers
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import yfinance as yf
except ImportError:
    sys.exit("yfinance not installed. Run: pip install --break-system-packages yfinance")

from db_init import load, today
from update_data import add_financials, add_valuation_snapshot, update_meta

_FX_CACHE = {}

def fx_to_usd(currency):
    """Return rate to multiply native-currency value by to get USD. 1.0 for USD/unknown."""
    if not currency or currency.upper() == "USD":
        return 1.0
    cur = currency.upper()
    if cur in _FX_CACHE:
        return _FX_CACHE[cur]
    rate = None
    try:
        info = yf.Ticker(f"{cur}USD=X").info
        rate = info.get("regularMarketPrice") or info.get("previousClose")
        if not rate:
            inv = yf.Ticker(f"USD{cur}=X").info
            inv_rate = inv.get("regularMarketPrice") or inv.get("previousClose")
            if inv_rate:
                rate = 1.0 / inv_rate
    except Exception as e:
        print(f"  WARN FX lookup failed for {cur}: {e}")
    if not rate:
        print(f"  WARN no FX rate for {cur}, leaving values in native currency")
        rate = 1.0
    _FX_CACHE[cur] = rate
    return rate


def fetch_one(ticker):
    info = yf.Ticker(ticker).info
    price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
    if price is None:
        print(f"  SKIP {ticker}: no price returned")
        return False

    currency = info.get("currency", "USD")
    fx = fx_to_usd(currency)

    # Money-denominated → convert to USD. Ratios/percentages stay as-is.
    price     = price * fx
    mcap      = info.get("marketCap")
    revenue   = info.get("totalRevenue")
    target    = info.get("targetMeanPrice")
    if mcap    is not None: mcap    = mcap    * fx
    if revenue is not None: revenue = revenue * fx
    if target  is not None: target  = target  * fx

    rev_growth = info.get("revenueGrowth")
    op_margin  = info.get("operatingMargins")
    debt_eq    = info.get("debtToEquity")
    pe         = info.get("trailingPE")
    ev_ebitda  = info.get("enterpriseToEbitda")
    chg_pct    = info.get("regularMarketChangePercent")
    ws_key     = info.get("recommendationKey")
    ws_count   = info.get("numberOfAnalystOpinions")
    ws_mean    = info.get("recommendationMean")

    upside = ((target - price) / price * 100) if target else None

    add_financials(
        ticker,
        stock_price=price,
        market_cap=mcap,
        pe_ratio=pe,
        revenue=revenue,
        revenue_growth=rev_growth * 100 if rev_growth is not None else None,
        operating_margin=op_margin * 100 if op_margin is not None else None,
        ev_ebitda=ev_ebitda,
        debt_to_equity=debt_eq / 100 if debt_eq is not None else None,
        price_change_pct=chg_pct,
        wallstreet_rating=ws_key,
        wallstreet_count=ws_count,
        wallstreet_mean=ws_mean,
        analyst_target=target,
        upside_pct=upside,
        currency_native=currency,
    )

    add_valuation_snapshot(
        ticker,
        price=price,
        pe=pe,
        ps=info.get("priceToSalesTrailing12Months"),
        ev_ebitda=ev_ebitda,
        market_cap=mcap,
        short_interest=info.get("shortPercentOfFloat"),
        analyst_target=target,
        upside=upside,
    )

    mcap_b = f"{mcap/1e9:.1f}B" if mcap else "n/a"
    pe_str = f"{pe:.1f}" if pe else "n/a"
    fx_tag = "" if fx == 1.0 else f"  [{currency}->USD @ {fx:.4f}]"
    print(f"  OK   {ticker:10s}  ${price:>8.2f}  mcap={mcap_b:>8}  pe={pe_str}{fx_tag}")
    return True


def fetch_all(tickers=None):
    companies = load("companies", [])
    public = [c for c in companies if c.get("public") and c.get("ticker")]
    if tickers:
        wanted = {t.upper() for t in tickers}
        public = [c for c in public if c["ticker"].upper() in wanted]
    print(f"Fetching {len(public)} tickers...")
    ok = 0
    for c in public:
        try:
            if fetch_one(c["ticker"]):
                ok += 1
        except Exception as e:
            print(f"  FAIL {c['ticker']}: {e}")
        time.sleep(0.2)
    print(f"Done: {ok}/{len(public)} succeeded")
    update_meta(last_updated=today())
    return ok


def main():
    args  = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    ok = fetch_all(args or None)
    if "--no-regen" not in flags and ok > 0:
        print("\nRegenerating HTML...")
        from update_data import regenerate_all
        regenerate_all()


if __name__ == "__main__":
    main()
