#!/usr/bin/env python3
"""Generate a morning news HTML brief for a given date from JSON data."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_init import load, today

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CSS = r"""
:root{--bg-primary:#0f1117;--bg-card:#1a1d28;--bg-header:#0a0c12;--bg-hover:#252836;--text-primary:#e8eaed;--text-secondary:#9aa0a6;--text-on-dark:#ffffff;--border:#2d3140;--accent-blue:#4C8BF5;--accent-green:#34A853;--accent-orange:#F9AB00;--accent-red:#EA4335;--accent-purple:#A142F4;--accent-cyan:#24C1E0;--accent-pink:#E8548C;--accent-teal:#1DB9A0;--positive:#34A853;--negative:#EA4335;--gap:16px;--radius:10px}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg-primary);color:var(--text-primary);line-height:1.6}
.container{max-width:1200px;margin:0 auto;padding:var(--gap)}
.header{background:linear-gradient(135deg,#1a1d28 0%,#0f1117 100%);border:1px solid var(--border);padding:28px 32px;border-radius:var(--radius);margin-bottom:var(--gap)}
.header h1{font-size:24px;font-weight:700;color:var(--text-on-dark)}
.header .date{font-size:14px;color:var(--accent-blue);margin-top:4px;font-weight:500}
.header .subtitle{font-size:13px;color:var(--text-secondary);margin-top:8px}
.back-link{display:inline-block;margin-bottom:var(--gap);color:var(--accent-blue);text-decoration:none;font-size:13px}
.back-link:hover{text-decoration:underline}
.alerts{display:flex;flex-direction:column;gap:10px;margin-bottom:24px}
.alert{background:var(--bg-card);border:1px solid var(--border);border-left:4px solid var(--accent-orange);border-radius:var(--radius);padding:14px 18px;display:flex;align-items:center;gap:12px}
.alert.bullish{border-left-color:var(--accent-green)}.alert.bearish{border-left-color:var(--accent-red)}.alert.neutral{border-left-color:var(--accent-blue)}
.alert-text{font-size:13px;color:var(--text-primary);flex:1}
.alert-tag{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;padding:2px 8px;border-radius:10px;flex-shrink:0}
.tag-energy{background:rgba(249,171,0,0.15);color:#F9AB00}
.tag-hardware{background:rgba(161,66,244,0.15);color:#A142F4}
.tag-software{background:rgba(76,139,245,0.15);color:#4C8BF5}
.tag-policy{background:rgba(36,193,224,0.15);color:#24C1E0}
.tag-finance{background:rgba(52,168,83,0.15);color:#34A853}
.tag-integration{background:rgba(29,185,160,0.15);color:#1DB9A0}
.tag-bubble{background:rgba(234,67,53,0.15);color:#EA4335}
.section{margin-bottom:24px}
.section-title{font-size:16px;font-weight:700;color:var(--text-on-dark);margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:10px}
.card-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:var(--gap)}
.card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);padding:20px;transition:border-color 0.2s}
.card:hover{border-color:var(--accent-blue)}
.card h3{font-size:14px;font-weight:600;color:var(--text-on-dark);margin-bottom:8px}
.card p{font-size:13px;color:var(--text-secondary);margin-bottom:8px}
.card .source{font-size:11px;color:var(--text-secondary);margin-top:10px;padding-top:8px;border-top:1px solid var(--border)}
.card .source a{color:var(--accent-blue);text-decoration:none}
.ticker{display:inline-block;font-size:11px;font-weight:600;color:var(--accent-blue);background:rgba(76,139,245,0.1);padding:1px 6px;border-radius:4px;margin-right:4px}
.ticker.up{color:var(--accent-green);background:rgba(52,168,83,0.1)}
.ticker.down{color:var(--accent-red);background:rgba(234,67,53,0.1)}
.ticker.warn{color:var(--accent-orange);background:rgba(249,171,0,0.1)}
.watchlist{width:100%;border-collapse:collapse;font-size:13px;margin-top:12px}
.watchlist th{text-align:left;padding:10px 12px;border-bottom:2px solid var(--border);color:var(--text-secondary);font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:0.5px}
.watchlist td{padding:10px 12px;border-bottom:1px solid var(--border)}
.watchlist tr:hover{background:var(--bg-hover)}
.val-up{color:var(--accent-green)}.val-down{color:var(--accent-red)}.val-flat{color:var(--text-secondary)}
.signal-badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:500;margin-right:4px}
.signal-bullish{background:rgba(52,168,83,0.15);color:#34A853}
.signal-bearish{background:rgba(234,67,53,0.15);color:#EA4335}
.signal-neutral{background:rgba(76,139,245,0.15);color:#4C8BF5}
"""

def generate_news(target_date=None):
    """Generate morning news HTML for the given date. Data must already be in the JSON files."""
    if target_date is None:
        target_date = today()

    news_entries = load("news_entries_" + target_date, [])
    if not news_entries:
        news_entries = load("news_entries", [])
        news_entries = [e for e in news_entries if e.get("date") == target_date]

    valuations = load("valuation_history", [])
    val_today = [v for v in valuations if v.get("date") == target_date]

    analyst = load("analyst_changes", [])
    analyst_today = [a for a in analyst if a.get("date") == target_date]

    signals = load("watchlist_signals", [])
    signals_today = [s for s in signals if s.get("date") == target_date]

    briefs = load("news_briefs", [])
    brief = None
    for b in briefs:
        if b.get("date") == target_date:
            brief = b
            break

    # Group news by sector
    sectors_order = ["energy","hardware","software","policy","integration","finance"]
    by_sector = {}
    for e in news_entries:
        s = e.get("sector","other").lower()
        by_sector.setdefault(s, []).append(e)

    html = []
    html.append(f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Morning Brief - {target_date}</title>
<style>{CSS}</style></head><body>
<div class="container">
<a href="../AI_Datacenter_Power_Landscape.html" class="back-link">&larr; Back to Dashboard</a>
<div class="header">
<h1>AI Industry Morning Brief</h1>
<div class="date">{target_date}</div>
<div class="subtitle">Daily intelligence covering energy, hardware, software, policy, integration &amp; financing for AI datacenter infrastructure</div>
</div>''')

    # Top alerts
    if news_entries:
        html.append('<div class="alerts">')
        for e in news_entries:
            sent = e.get("sentiment","neutral")
            sector = e.get("sector","").lower()
            tag_class = f"tag-{sector}" if sector in ["energy","hardware","software","policy","finance","integration"] else "tag-energy"
            html.append(f'<div class="alert {sent}"><div class="alert-text"><strong>{e.get("headline","")}</strong> &mdash; {e.get("summary","")}</div><span class="alert-tag {tag_class}">{e.get("sector","").upper()}</span></div>')
        html.append('</div>')

    # Sector-by-sector cards
    sector_labels = {"energy":"Energy & Power","hardware":"Hardware & Semiconductors","software":"Software & AI Models","policy":"Policy & Regulation","integration":"Integration & Infrastructure","finance":"Financing & Markets"}
    for sec in sectors_order:
        items = by_sector.get(sec, [])
        if not items:
            continue
        html.append(f'<div class="section"><div class="section-title">{sector_labels.get(sec, sec.title())}</div><div class="card-grid">')
        for item in items:
            source_html = ""
            if item.get("source_name") or item.get("source_url"):
                url = item.get("source_url","#")
                name = item.get("source_name","Source")
                source_html = f'<div class="source"><a href="{url}">{name}</a></div>'
            html.append(f'<div class="card"><h3>{item.get("headline","")}</h3><p>{item.get("summary","")}</p>{source_html}</div>')
        html.append('</div></div>')

    # ── NEW: Valuation Tracker ──
    if val_today:
        html.append('<div class="section"><div class="section-title">Valuation Tracker - Daily Snapshot</div>')
        html.append('<div class="card"><table class="watchlist"><thead><tr><th>Ticker</th><th>Price</th><th>P/E</th><th>P/S</th><th>EV/EBITDA</th><th>Mkt Cap</th><th>Short Int</th><th>Avg Target</th><th>Upside</th></tr></thead><tbody>')
        for v in val_today:
            upside = v.get("upside_pct") or 0
            up_class = "val-up" if upside and upside > 5 else "val-down" if upside and upside < -5 else "val-flat"
            up_str = f"+{upside:.1f}%" if upside and upside > 0 else f"{upside:.1f}%" if upside else "N/A"
            mc = v.get("market_cap")
            if mc is None:
                mc_str = "N/A"
            elif isinstance(mc, str):
                mc_str = f"${mc}" if not mc.startswith("$") else mc
            elif isinstance(mc, (int, float)) and mc > 1e6:
                mc_str = f"${mc/1e9:.0f}B"
            else:
                mc_str = f"${mc}"
            si = v.get("short_interest")
            si_str = f"{si}%" if si is not None else "N/A"
            at = v.get("avg_analyst_target")
            at_str = f"${at:.0f}" if at else "N/A"
            pr = v.get("price", 0) or 0
            html.append(f'<tr><td><span class="ticker">{v.get("ticker","")}</span></td>'
                       f'<td>${pr:.2f}</td>'
                       f'<td>{v.get("pe_ratio") or "N/A"}</td>'
                       f'<td>{v.get("ps_ratio") or "N/A"}</td>'
                       f'<td>{v.get("ev_ebitda") or "N/A"}</td>'
                       f'<td>{mc_str}</td>'
                       f'<td>{si_str}</td>'
                       f'<td>{at_str}</td>'
                       f'<td class="{up_class}">{up_str}</td></tr>')
        html.append('</tbody></table></div></div>')

    # ── NEW: Sentiment & Momentum ──
    if analyst_today or signals_today:
        html.append('<div class="section"><div class="section-title">Sentiment &amp; Momentum Signals</div><div class="card-grid">')
        if analyst_today:
            html.append('<div class="card"><h3>Analyst Rating Changes</h3>')
            for a in analyst_today:
                direction = ""
                if a.get("new_target") and a.get("old_target"):
                    if a["new_target"] > a["old_target"]:
                        direction = '<span class="val-up">&#9650;</span>'
                    else:
                        direction = '<span class="val-down">&#9660;</span>'
                old_t = a.get("old_target")
                new_t = a.get("new_target")
                old_t_str = f"${old_t:.0f}" if old_t is not None else "N/A"
                new_t_str = f"${new_t:.0f}" if new_t is not None else "N/A"
                html.append(f'<p><span class="ticker">{a.get("ticker","")}</span> {a.get("firm","")}: '
                           f'{a.get("old_rating","N/A")} &rarr; <strong>{a.get("new_rating","")}</strong> | '
                           f'PT: {old_t_str} &rarr; {new_t_str} {direction}</p>')
            html.append('</div>')
        if signals_today:
            html.append('<div class="card"><h3>Watchlist Signals</h3>')
            for s in signals_today:
                stype = s.get("signal_type","")
                badge_class = "signal-bullish" if stype in ["undervalued","insider_buy","short_squeeze"] else "signal-bearish" if stype in ["overvalued","insider_sell"] else "signal-neutral"
                html.append(f'<p><span class="ticker">{s.get("ticker","")}</span> <span class="signal-badge {badge_class}">{stype.replace("_"," ").title()}</span> {s.get("description","")}</p>')
            html.append('</div>')
        html.append('</div></div>')

    # Watchlist summary table
    if brief and brief.get("tickers"):
        html.append('<div class="section"><div class="section-title">Watchlist</div>')
        html.append('<div class="card"><table class="watchlist"><thead><tr><th>Ticker</th><th>Direction</th><th>Signal</th></tr></thead><tbody>')
        for t in brief.get("tickers",[]):
            d = t.get("direction","neutral")
            cls = "up" if d=="up" else "down" if d=="down" else ""
            note = t.get("note","")
            html.append(f'<tr><td><span class="ticker {cls}">{t["ticker"]}</span></td><td>{d.title()}</td><td>{note}</td></tr>')
        html.append('</tbody></table></div></div>')

    html.append(f'''<div style="text-align:center;padding:16px;color:var(--text-secondary);font-size:11px;border-top:1px solid var(--border);margin-top:24px">
AI Morning Brief &bull; {target_date} &bull; Generated from investment landscape data store<br>
Sources cited per item. Not investment advice.</div>
</div></body></html>''')

    # Write file
    news_dir = os.path.join(BASE_DIR, "morning-news")
    os.makedirs(news_dir, exist_ok=True)
    out_path = os.path.join(news_dir, f"{target_date}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html))
    print(f"News brief written to {out_path}")

    # Update news_briefs archive
    briefs = load("news_briefs", [])
    existing = [b for b in briefs if b.get("date") != target_date]
    headlines = " | ".join([e.get("headline","") for e in news_entries[:5]])
    sectors_covered = list(set([e.get("sector","") for e in news_entries if e.get("sector")]))
    new_brief = {
        "date": target_date,
        "top_headlines": headlines,
        "sectors": sectors_covered,
        "tickers": brief.get("tickers",[]) if brief else [],
        "signals": brief.get("signals",[]) if brief else [],
        "file": f"morning-news/{target_date}.html"
    }
    existing.append(new_brief)
    from db_init import save
   