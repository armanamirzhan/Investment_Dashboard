#!/usr/bin/env python3
"""
Data update helper for the scheduled task.
Provides functions to update any part of the data store.
The scheduled task calls these after researching.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_init import load, save, today, now

def update_kpi(key, value=None, subtitle=None, numeric=None):
    """Update a single KPI metric."""
    kpis = load("kpi_metrics", [])
    for k in kpis:
        if k["key"] == key:
            if value is not None: k["value"] = value
            if subtitle is not None: k["subtitle"] = subtitle
            if numeric is not None: k["numeric"] = numeric
            k["updated"] = today()
            break
    save("kpi_metrics", kpis)

def update_company(ticker, **kwargs):
    """Update fields on a company."""
    companies = load("companies", [])
    for c in companies:
        if c["ticker"] == ticker:
            c.update(kwargs)
            c["updated"] = today()
            break
    save("companies", companies)

def add_company(ticker, name, sector, **kwargs):
    """Add a new company to tracking."""
    companies = load("companies", [])
    if any(c["ticker"] == ticker for c in companies):
        return update_company(ticker, name=name, sector=sector, **kwargs)
    companies.append({"ticker":ticker, "name":name, "sector":sector, "updated":today(), **kwargs})
    save("companies", companies)

def add_financials(ticker, **metrics):
    """Add a financial snapshot for today."""
    fins = load("financials", [])
    entry = {"ticker": ticker, "date": today()}
    entry.update(metrics)
    # Replace if same ticker+date exists
    fins = [f for f in fins if not (f["ticker"]==ticker and f["date"]==today())]
    fins.append(entry)
    save("financials", fins)

def add_valuation_snapshot(ticker, price, pe=None, ps=None, ev_ebitda=None, market_cap=None, short_interest=None, analyst_target=None, upside=None):
    """Add a daily valuation snapshot for tracking."""
    vals = load("valuation_history", [])
    entry = {"date":today(),"ticker":ticker,"price":price,"pe_ratio":pe,"ps_ratio":ps,"ev_ebitda":ev_ebitda,"market_cap":market_cap,"short_interest":short_interest,"avg_analyst_target":analyst_target,"upside_pct":upside}
    vals = [v for v in vals if not (v["ticker"]==ticker and v["date"]==today())]
    vals.append(entry)
    save("valuation_history", vals)

def add_analyst_change(ticker, firm, new_rating, new_target, old_rating=None, old_target=None):
    """Record an analyst rating change."""
    changes = load("analyst_changes", [])
    changes.append({"date":today(),"ticker":ticker,"firm":firm,"new_rating":new_rating,"new_target":new_target,"old_rating":old_rating,"old_target":old_target})
    save("analyst_changes", changes)

def add_watchlist_signal(ticker, signal_type, description, severity="medium"):
    """Add a watchlist signal (undervalued, overvalued, momentum, insider_buy, etc)."""
    signals = load("watchlist_signals", [])
    signals.append({"date":today(),"ticker":ticker,"signal_type":signal_type,"description":description,"severity":severity})
    save("watchlist_signals", signals)

def add_news_entry(headline, summary, sector, sentiment="neutral", source_name=None, source_url=None):
    """Add a news entry for today's brief."""
    key = f"news_entries_{today()}"
    entries = load(key, [])
    entries.append({"date":today(),"headline":headline,"summary":summary,"sector":sector,"sentiment":sentiment,"source_name":source_name,"source_url":source_url})
    save(key, entries)

def update_news_brief_tickers(tickers_list, signals_list):
    """Update the brief-level ticker and signal summaries."""
    briefs = load("news_briefs", [])
    found = False
    for b in briefs:
        if b.get("date") == today():
            b["tickers"] = tickers_list
            b["signals"] = signals_list
            found = True
            break
    if not found:
        briefs.append({"date":today(),"tickers":tickers_list,"signals":signals_list,"file":f"morning-news/{today()}.html"})
    save("news_briefs", briefs)

def update_buildout(ticker, **kwargs):
    """Update a hyperscaler buildout entry."""
    buildouts = load("hyperscaler_buildouts", [])
    for b in buildouts:
        if b["ticker"] == ticker:
            b.update(kwargs)
            b["updated"] = today()
            break
    save("hyperscaler_buildouts", buildouts)

def update_chart(chart_id, **kwargs):
    """Update chart data. Pass datasets, labels, etc."""
    charts = load("chart_data", {})
    if chart_id in charts:
        charts[chart_id].update(kwargs)
    save("chart_data", charts)

def update_risk(title, **kwargs):
    """Update a risk entry by title."""
    risks = load("risks", [])
    for r in risks:
        if r["title"] == title:
            r.update(kwargs)
            r["updated"] = today()
            break
    save("risks", risks)

def update_meta(**kwargs):
    """Update dashboard metadata (last_updated, etc)."""
    meta = load("meta", {})
    meta.update(kwargs)
    save("meta", meta)

def regenerate_all():
    """Run all generators to rebuild HTML from data."""
    from generate_dashboard import generate as gen_dash
    from generate_news import generate_news as gen_news
    from generate_reports import generate_all as gen_reports

    update_meta(last_updated=now())
    gen_dash()
    gen_news(today())
    gen_reports()
    print("All files regenerated")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "regenerate":
        regenerate_all()
    else:
        print("Usage: python update_data.py regenerate")
        print("Or import and call individual functions from the scheduled task")
