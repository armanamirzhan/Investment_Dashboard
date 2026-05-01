#!/usr/bin/env python3
"""Generate the main dashboard HTML from JSON data files."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_init import load, today, DATA_DIR

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(BASE_DIR, "AI_Datacenter_Power_Landscape.html")

SECTOR_META = {
    "software":         {"label": "AI Software",                "icon": "💻", "color": "#A142F4"},
    "hyperscaler":      {"label": "Hyperscalers",               "icon": "☁️", "color": "#4C8BF5"},
    "electricity":      {"label": "Electricity Infrastructure", "icon": "⚡", "color": "#F9AB00"},
    "dc_hardware":      {"label": "Datacenter Hardware",        "icon": "🔧", "color": "#34A853"},
    "semiconductor_fab":{"label": "Semiconductor Fabrication",  "icon": "🏭", "color": "#EA4335"},
}

CSS = r"""
:root{--bg-primary:#0f1117;--bg-card:#1a1d28;--bg-header:#0a0c12;--bg-hover:#252836;--text-primary:#e8eaed;--text-secondary:#9aa0a6;--text-on-dark:#ffffff;--border:#2d3140;--accent-blue:#4C8BF5;--accent-green:#34A853;--accent-orange:#F9AB00;--accent-red:#EA4335;--accent-purple:#A142F4;--accent-cyan:#24C1E0;--accent-pink:#E8548C;--accent-teal:#1DB9A0;--positive:#34A853;--negative:#EA4335;--gap:16px;--radius:10px}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg-primary);color:var(--text-primary);line-height:1.5}
.dashboard-container{max-width:1500px;margin:0 auto;padding:var(--gap)}
.dashboard-header{background:linear-gradient(135deg,#1a1d28 0%,#0f1117 100%);border:1px solid var(--border);padding:24px 28px;border-radius:var(--radius);margin-bottom:var(--gap);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px}
.dashboard-header h1{font-size:22px;font-weight:700;color:var(--text-on-dark)}
.dashboard-header .subtitle{font-size:13px;color:var(--text-secondary);margin-top:4px}
.filters{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.filter-group{display:flex;align-items:center;gap:6px}
.filter-group label{font-size:11px;color:var(--text-secondary);text-transform:uppercase;letter-spacing:0.5px}
.filter-group select{padding:6px 10px;border:1px solid var(--border);border-radius:6px;background:var(--bg-hover);color:var(--text-primary);font-size:13px;cursor:pointer}
.filter-group select:focus{outline:none;border-color:var(--accent-blue)}
.tabs{display:flex;gap:4px;margin-bottom:var(--gap);flex-wrap:wrap}
.tab{padding:10px 20px;border-radius:8px;border:1px solid var(--border);background:var(--bg-card);color:var(--text-secondary);cursor:pointer;font-size:13px;font-weight:500;transition:all 0.2s}
.tab:hover{background:var(--bg-hover);color:var(--text-primary)}
.tab.active{background:var(--accent-blue);color:#fff;border-color:var(--accent-blue)}
.tab-content{display:none}.tab-content.active{display:block}
.kpi-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:var(--gap);margin-bottom:var(--gap)}
.kpi-card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);padding:20px 24px}
.kpi-label{font-size:11px;color:var(--text-secondary);text-transform:uppercase;letter-spacing:0.8px;margin-bottom:6px}
.kpi-value{font-size:28px;font-weight:700;color:var(--text-on-dark);margin-bottom:4px}
.kpi-sub{font-size:12px;color:var(--text-secondary)}
.kpi-card.highlight{border-left:3px solid var(--accent-blue)}
.chart-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:var(--gap);margin-bottom:var(--gap)}
.chart-container{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);padding:20px 24px}
.chart-container h3{font-size:14px;font-weight:600;color:var(--text-primary);margin-bottom:16px}
.chart-container canvas{max-height:320px}
.chart-container.full-width{grid-column:1/-1}
.table-section{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);padding:20px 24px;overflow-x:auto;margin-bottom:var(--gap)}
.table-section h3{font-size:14px;font-weight:600;margin-bottom:16px}
.data-table{width:100%;border-collapse:collapse;font-size:13px}
.data-table thead th{text-align:left;padding:10px 12px;border-bottom:2px solid var(--border);color:var(--text-secondary);font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;white-space:nowrap;user-select:none;cursor:pointer}
.data-table thead th:hover{color:var(--text-primary)}
.data-table tbody td{padding:10px 12px;border-bottom:1px solid var(--border)}
.data-table tbody tr:hover{background:var(--bg-hover)}
.badge{display:inline-block;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:500}
.badge-nuclear{background:rgba(161,66,244,0.15);color:#A142F4}
.badge-gas{background:rgba(249,171,0,0.15);color:#F9AB00}
.badge-solar{background:rgba(52,168,83,0.15);color:#34A853}
.badge-wind{background:rgba(36,193,224,0.15);color:#24C1E0}
.badge-grid{background:rgba(76,139,245,0.15);color:#4C8BF5}
.badge-fusion{background:rgba(232,84,140,0.15);color:#E8548C}
.badge-smr{background:rgba(161,66,244,0.25);color:#c77dff}
.badge-storage{background:rgba(29,185,160,0.15);color:#1DB9A0}
.badge-sub{display:inline-block;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:500;background:rgba(255,255,255,0.06);color:var(--text-secondary)}
.rating-strong_buy{color:#34A853;font-weight:700}.rating-buy{color:#4C8BF5;font-weight:600}.rating-hold{color:#F9AB00;font-weight:600}.rating-sell{color:#EA4335;font-weight:600}
.source-note{font-size:11px;color:var(--text-secondary);margin-top:8px;padding-top:8px;border-top:1px solid var(--border)}
.risk-indicator{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}
.risk-high{background:var(--accent-red)}.risk-medium{background:var(--accent-orange)}.risk-low{background:var(--accent-green)}
.section-divider{font-size:16px;font-weight:700;color:var(--text-on-dark);margin:24px 0 16px;padding-bottom:8px;border-bottom:1px solid var(--border)}
.info-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:var(--gap);margin-bottom:var(--gap)}
.info-card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);padding:20px}
.info-card h4{font-size:14px;font-weight:600;margin-bottom:12px;color:var(--accent-blue)}
.info-card p{font-size:13px;color:var(--text-secondary);margin-bottom:8px}
.info-card .metric{font-size:20px;font-weight:700;color:var(--text-on-dark)}
.ticker{font-size:11px;color:var(--accent-blue);font-weight:600;background:rgba(76,139,245,0.1);padding:2px 6px;border-radius:4px}
.private-badge{font-size:11px;color:var(--text-secondary);background:rgba(255,255,255,0.06);padding:2px 6px;border-radius:4px}
.sector-header{display:flex;align-items:center;gap:10px;margin-bottom:16px;padding:12px 16px;background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius)}
.sector-header .sector-icon{font-size:24px}
.sector-header h2{font-size:18px;font-weight:700;color:var(--text-on-dark)}
.sector-header .sector-count{font-size:12px;color:var(--text-secondary);margin-left:8px}
footer.dashboard-footer{text-align:center;padding:16px;color:var(--text-secondary);font-size:11px;border-top:1px solid var(--border);margin-top:24px}
@media(max-width:768px){.dashboard-header{flex-direction:column;align-items:flex-start}.kpi-row{grid-template-columns:repeat(2,1fr)}.chart-row{grid-template-columns:1fr}.filters{flex-direction:column;align-items:flex-start}}
@media print{body{background:#fff;color:#000}.dashboard-container{max-width:none}.tab-content{display:block!important}.tabs{display:none}}
.live-price,.live-mcap{font-variant-numeric:tabular-nums;white-space:nowrap}
.live-change{font-variant-numeric:tabular-nums;white-space:nowrap;font-weight:600}
.live-change.positive{color:var(--positive)}.live-change.negative{color:var(--negative)}
.live-pe{font-variant-numeric:tabular-nums}
.live-loading{color:var(--text-secondary);font-size:11px;animation:pulse 1.5s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:0.4}50%{opacity:1}}
.live-status{position:fixed;bottom:16px;right:16px;background:var(--bg-card);border:1px solid var(--border);border-radius:8px;padding:8px 14px;font-size:11px;color:var(--text-secondary);z-index:100;display:flex;align-items:center;gap:6px;transition:opacity 0.3s}
.live-status .dot{width:6px;height:6px;border-radius:50%;display:inline-block}
.live-status .dot.ok{background:var(--positive)}.live-status .dot.err{background:var(--negative)}.live-status .dot.loading{background:var(--accent-orange);animation:pulse 1s ease-in-out infinite}
"""

def badge_html(text, btype):
    return f'<span class="badge badge-{btype}">{text}</span>'

def make_badges(buildout):
    parts = []
    for txt, typ in zip(buildout.get("energy_badges",[]), buildout.get("energy_types",[])):
        parts.append(badge_html(txt, typ))
    return " ".join(parts)

def link_wrap(text, report, ticker=None):
    tk = f' <span class="ticker">{ticker}</span>' if ticker else ''
    if report:
        return f'<a href="{report}" style="color:var(--text-on-dark);text-decoration:none;border-bottom:1px dashed var(--accent-blue)"><strong>{text}</strong></a>{tk}'
    return f'<strong>{text}</strong>{tk}'

def rating_html(rating, emoji):
    if not rating:
        return '<span style="color:var(--text-secondary)">—</span>'
    cls = f"rating-{rating.lower()}"
    label = rating.replace("_"," ").title()
    e = emoji or ""
    return f'{e} <span class="{cls}">{label}</span>'

def ticker_html(ticker, public):
    if ticker:
        return f'<span class="ticker">{ticker}</span>'
    if not public:
        return '<span class="private-badge">Private</span>'
    return '—'

def company_table(companies, sector, extra_cols=None):
    """Generate a company table for a given sector with live data columns."""
    rows = [c for c in companies if c["sector"] == sector]
    if not rows:
        return ""
    # Group by sub_sector
    sub_sectors = []
    seen = set()
    for c in rows:
        ss = c.get("sub_sector","Other")
        if ss not in seen:
            sub_sectors.append(ss)
            seen.add(ss)

    html = []
    html.append('<div class="table-section">')
    sm = SECTOR_META.get(sector, {})
    count = len(rows)
    html.append(f'<div class="sector-header"><span class="sector-icon">{sm.get("icon","")}</span><h2>{sm.get("label",sector)}</h2><span class="sector-count">{count} companies tracked</span></div>')
    html.append(f'<table class="data-table" id="table-{sector}"><thead><tr>')
    headers = ["Company","Ticker","Price","Change","Mkt Cap","P/E","Rating","Thesis"]
    ncols = len(headers)
    for h in headers:
        html.append(f'<th>{h}</th>')
    html.append('</tr></thead><tbody>')

    for ss in sub_sectors:
        ss_rows = [c for c in rows if c.get("sub_sector","Other") == ss]
        # Sub-sector separator row
        html.append(f'<tr data-separator="1"><td colspan="{ncols}" style="background:var(--bg-hover);padding:8px 12px;font-weight:600;color:{sm.get("color","var(--accent-blue)")};font-size:12px;text-transform:uppercase;letter-spacing:0.5px">{ss} ({len(ss_rows)})</td></tr>')
        for c in ss_rows:
            ticker = c.get("ticker","")
            name = link_wrap(c["name"], c.get("report"), None)
            tk = ticker_html(ticker, c.get("public", True))
            rat = rating_html(c.get("rating"), c.get("emoji"))
            thesis = c.get("thesis","")
            if len(thesis) > 180:
                thesis = thesis[:180] + "…"
            # data-ticker attribute enables live JS updates
            row_attr = f' data-ticker="{ticker}"' if ticker else ''
            html.append(f'<tr{row_attr}>'
                f'<td>{name}</td>'
                f'<td>{tk}</td>'
                f'<td class="live-price" data-field="price">—</td>'
                f'<td class="live-change" data-field="change">—</td>'
                f'<td class="live-mcap" data-field="mktCap">—</td>'
                f'<td class="live-pe" data-field="pe">—</td>'
                f'<td>{rat}</td>'
                f'<td style="max-width:360px;font-size:12px;color:var(--text-secondary)">{thesis}</td>'
                f'</tr>')

    html.append('</tbody></table></div>')
    return "\n".join(html)


def generate():
    meta = load("meta", {})
    kpis = load("kpi_metrics", [])
    companies = load("companies", [])
    buildouts = load("hyperscaler_buildouts", [])
    power = load("power_suppliers", [])
    hardware = load("hardware_suppliers", [])
    nuclear = load("nuclear_tracker", [])
    fusion = load("fusion_tracker", [])
    haleu = load("haleu_constraint", {})
    risks = load("risks", [])
    charts = load("chart_data", {})
    briefs = load("news_briefs", [])

    html = []
    html.append(f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{meta.get("title","AI Investment Landscape Dashboard")}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.1"></script>
<style>{CSS}</style>
</head>
<body>
<div class="dashboard-container">
<header class="dashboard-header">
<div>
<h1>{meta.get("title","AI Investment Landscape")}</h1>
<div class="subtitle">{meta.get("subtitle","")} &bull; Data as of {meta.get("last_updated","")} &bull; 5-Category Investment Taxonomy</div>
</div>
<div class="filters">
<div class="filter-group"><label>Filter</label>
<select id="filter-sector" onchange="filterSector(this.value)">
<option value="all">All Categories</option>
<option value="software">💻 AI Software</option>
<option value="hyperscaler">☁️ Hyperscalers</option>
<option value="electricity">⚡ Electricity Infrastructure</option>
<option value="dc_hardware">🔧 Datacenter Hardware</option>
<option value="semiconductor_fab">🏭 Semiconductor Fabrication</option>
</select></div>
<div class="filter-group"><label>Rating</label>
<select id="filter-rating" onchange="filterRating(this.value)">
<option value="all">All Ratings</option>
<option value="STRONG_BUY">🟢 Strong Buy</option>
<option value="BUY">🟡 Buy</option>
<option value="HOLD">🟠 Hold</option>
<option value="SELL">🔴 Sell</option>
</select></div>
</div>
</header>''')

    # KPI Row
    html.append('<section class="kpi-row">')
    # Auto-generate sector KPIs from companies data
    from collections import Counter
    sector_counts = Counter(c["sector"] for c in companies)
    public_count = sum(1 for c in companies if c.get("public"))
    private_count = len(companies) - public_count
    rated = [c for c in companies if c.get("rating")]
    buy_count = sum(1 for c in rated if c["rating"] in ("STRONG_BUY","BUY"))

    auto_kpis = [
        {"label": "Total Companies Tracked", "value": str(len(companies)), "subtitle": f"{public_count} public · {private_count} private", "highlight": True},
        {"label": "Buy/Strong Buy Ratings", "value": str(buy_count), "subtitle": f"of {len(rated)} rated companies"},
    ]
    for sector_key in ["software","hyperscaler","electricity","dc_hardware","semiconductor_fab"]:
        sm = SECTOR_META[sector_key]
        auto_kpis.append({
            "label": f"{sm['icon']} {sm['label']}",
            "value": str(sector_counts.get(sector_key,0)),
            "subtitle": "companies tracked"
        })

    for k in auto_kpis:
        hl = ' highlight' if k.get("highlight") else ''
        html.append(f'<div class="kpi-card{hl}"><div class="kpi-label">{k["label"]}</div><div class="kpi-value">{k["value"]}</div><div class="kpi-sub">{k["subtitle"]}</div></div>')
    html.append('</section>')

    # Tabs
    html.append('''<div class="tabs">
<div class="tab active" onclick="switchTab('overview')">📊 Overview</div>
<div class="tab" onclick="switchTab('software')">💻 AI Software</div>
<div class="tab" onclick="switchTab('hyperscaler')">☁️ Hyperscalers</div>
<div class="tab" onclick="switchTab('electricity')">⚡ Electricity</div>
<div class="tab" onclick="switchTab('dc_hardware')">🔧 Hardware</div>
<div class="tab" onclick="switchTab('semiconductor_fab')">🏭 Semicond Fab</div>
<div class="tab" onclick="switchTab('nuclear')">☢️ Nuclear & Fusion</div>
<div class="tab" onclick="switchTab('risks')">⚠️ Risks</div>
<div class="tab" onclick="switchTab('morningnews')" style="margin-left:auto;background:var(--accent-purple);color:#fff;border-color:var(--accent-purple);">📰 Morning News</div>
</div>''')

    # ── TAB: Overview ──
    html.append('<div class="tab-content active" id="tab-overview">')
    # Charts from chart_data
    c = charts.get("demand_projections",{})
    html.append(f'<div class="chart-row"><div class="chart-container"><h3>{c.get("title","")}</h3><canvas id="chart-demand"></canvas><div class="source-note">{c.get("source","")}</div></div>')
    c = charts.get("energy_mix",{})
    html.append(f'<div class="chart-container"><h3>{c.get("title","")}</h3><canvas id="chart-energymix"></canvas><div class="source-note">{c.get("source","")}</div></div></div>')
    # CapEx trajectory
    c = charts.get("capex_trajectory",{})
    html.append(f'<div class="chart-row"><div class="chart-container full-width"><h3>{c.get("title","")}</h3><canvas id="chart-capex"></canvas><div class="source-note">{c.get("source","")}</div></div></div>')
    # Sector distribution chart
    html.append('<div class="chart-row"><div class="chart-container"><h3>Companies by Category</h3><canvas id="chart-sector-dist"></canvas></div>')
    html.append('<div class="chart-container"><h3>Ratings Distribution</h3><canvas id="chart-rating-dist"></canvas></div></div>')
    # Clean energy + timeline
    c1 = charts.get("clean_energy",{})
    c2 = charts.get("power_timeline",{})
    html.append(f'<div class="chart-row"><div class="chart-container"><h3>{c1.get("title","")}</h3><canvas id="chart-cleanenergy"></canvas><div class="source-note">{c1.get("source","")}</div></div>')
    html.append(f'<div class="chart-container"><h3>{c2.get("title","")}</h3><canvas id="chart-timeline"></canvas><div class="source-note">{c2.get("source","")}</div></div></div>')
    html.append('</div>')

    # ── TAB: Software ──
    html.append('<div class="tab-content" id="tab-software">')
    html.append(company_table(companies, "software"))
    html.append('</div>')

    # ── TAB: Hyperscalers ──
    html.append('<div class="tab-content" id="tab-hyperscaler">')
    html.append(company_table(companies, "hyperscaler"))
    # Buildout tracker table
    if buildouts:
        html.append('<div class="table-section" style="margin-top:var(--gap)"><h3>Hyperscaler Datacenter Buildout Tracker</h3>')
        html.append('<table class="data-table" id="table-buildouts"><thead><tr>')
        for h in ["Company","2025 CapEx ($B)","2026E CapEx ($B)","Current Power","Target Power","Target Year","Energy Strategy"]:
            html.append(f'<th>{h}</th>')
        html.append('</tr></thead><tbody>')
        for b in buildouts:
            tk = b.get("ticker","")
            badges = make_badges(b)
            name_html = link_wrap(b["name"], b.get("report"), tk)
            html.append(f'<tr><td>{name_html}</td><td>${b["capex_2025"]}B</td><td>${b["capex_2026e"]}B</td><td>{b["current_power"]}</td><td>{b["target_power"]}</td><td>{b["target_year"]}</td><td>{badges}</td></tr>')
        html.append('</tbody></table></div>')
        # Buildout charts
        html.append('<div class="chart-row"><div class="chart-container"><h3>Hyperscaler Power Capacity Targets (GW)</h3><canvas id="chart-hscaler-power"></canvas></div>')
        html.append('<div class="chart-container"><h3>Hyperscaler CapEx Comparison 2025 vs 2026E ($B)</h3><canvas id="chart-hscaler-capex"></canvas></div></div>')
        # Info cards
        html.append('<div class="info-grid">')
        for b in buildouts:
            if b.get("detail_title"):
                html.append(f'<div class="info-card"><h4>{b["detail_title"]}</h4><p>{b["detail_html"]}</p><div class="source-note">{b["detail_source"]}</div></div>')
        html.append('</div>')
    html.append('</div>')

    # ── TAB: Electricity ──
    html.append('<div class="tab-content" id="tab-electricity">')
    html.append(company_table(companies, "electricity"))
    # Power suppliers table (legacy data)
    if power:
        html.append('<div class="table-section" style="margin-top:var(--gap)"><h3>Power Supplier Detail &mdash; Datacenter Exposure</h3>')
        html.append('<table class="data-table"><thead><tr><th>Company</th><th>Ticker</th><th>Segment</th><th>DC Revenue Exposure</th><th>Key DC Deals</th><th>Capacity / Backlog</th><th>Outlook</th></tr></thead><tbody>')
        for p in power:
            name_html = link_wrap(p["company"], p.get("report"), None)
            tk = f'<span class="ticker">{p["ticker"]}</span>' if p.get("ticker") else "Private"
            html.append(f'<tr><td>{name_html}</td><td>{tk}</td><td>{p["segment"]}</td><td>{p["exposure"]}</td><td>{p["deals"]}</td><td>{p["backlog"]}</td><td>{p["outlook"]}</td></tr>')
        html.append('</tbody></table></div>')
    # Charts
    c1 = charts.get("turbine_backlog",{})
    c2 = charts.get("nuclear_ppas",{})
    if c1 or c2:
        html.append(f'<div class="chart-row"><div class="chart-container"><h3>{c1.get("title","")}</h3><canvas id="chart-turbine-backlog"></canvas><div class="source-note">{c1.get("source","")}</div></div>')
        html.append(f'<div class="chart-container"><h3>{c2.get("title","")}</h3><canvas id="chart-nuclear-ppas"></canvas><div class="source-note">{c2.get("source","")}</div></div></div>')
    html.append('</div>')

    # ── TAB: Datacenter Hardware ──
    html.append('<div class="tab-content" id="tab-dc_hardware">')
    html.append(company_table(companies, "dc_hardware"))
    # Legacy hardware suppliers table
    if hardware:
        html.append('<div class="table-section" style="margin-top:var(--gap)"><h3>Hardware Supplier Detail</h3>')
        html.append('<table class="data-table"><thead><tr><th>Company</th><th>Ticker</th><th>Category</th><th>Product / Role</th><th>Relevance</th><th>Key Metrics</th></tr></thead><tbody>')
        for h in hardware:
            name_html = link_wrap(h["company"], h.get("report"), None)
            tk = f'<span class="ticker">{h["ticker"]}</span>' if h.get("ticker") else ""
            html.append(f'<tr><td>{name_html}</td><td>{tk}</td><td>{h["category"]}</td><td>{h["product"]}</td><td>{h["relevance"]}</td><td>{h["metrics"]}</td></tr>')
        html.append('</tbody></table></div>')
    c1 = charts.get("sic_market",{})
    c2 = charts.get("lead_times",{})
    if c1 or c2:
        html.append(f'<div class="chart-row"><div class="chart-container"><h3>{c1.get("title","")}</h3><canvas id="chart-sic"></canvas><div class="source-note">{c1.get("source","")}</div></div>')
        html.append(f'<div class="chart-container"><h3>{c2.get("title","")}</h3><canvas id="chart-leadtimes"></canvas><div class="source-note">{c2.get("source","")}</div></div></div>')
    html.append('</div>')

    # ── TAB: Semiconductor Fabrication ──
    html.append('<div class="tab-content" id="tab-semiconductor_fab">')
    html.append(company_table(companies, "semiconductor_fab"))
    html.append('</div>')

    # ── TAB: Nuclear ──
    html.append('<div class="tab-content" id="tab-nuclear">')
    html.append('<div class="section-divider">Small Modular Reactors (SMRs) &amp; Advanced Nuclear</div>')
    html.append('<div class="table-section"><h3>SMR &amp; Advanced Nuclear Developer Tracker</h3>')
    html.append('<table class="data-table" id="table-smr"><thead><tr><th>Company</th><th>Ticker</th><th>Technology</th><th>Capacity</th><th>NRC Status</th><th>First Commercial</th><th>Key Datacenter Partners</th></tr></thead><tbody>')
    for n in nuclear:
        name_html = link_wrap(n["company"], n.get("report"), None)
        tk = f'<span class="ticker">{n["ticker"]}</span>' if n.get("ticker") else "Private"
        html.append(f'<tr><td>{name_html}</td><td>{tk}</td><td>{n["technology"]}</td><td>{n["capacity"]}</td><td>{n["nrc_status"]}</td><td>{n["first_commercial"]}</td><td>{n["dc_partners"]}</td></tr>')
    html.append('</tbody></table>')
    nc = charts.get("nuclear_timeline",{})
    html.append(f'<div class="source-note">{nc.get("source","")}</div></div>')
    # Fusion
    html.append('<div class="section-divider">Fusion Energy</div><div class="info-grid">')
    for f in fusion:
        html.append(f'<div class="info-card"><h4>{f["company"]}</h4>')
        html.append(f'<p><strong>Technology:</strong> {f["technology"]}</p>')
        html.append(f'<p><strong>Timeline:</strong> {f["timeline"]}</p>')
        html.append(f'<p><strong>Datacenter Connection:</strong> {f["dc_connection"]}</p>')
        html.append(f'<p><strong>Funding:</strong> {f["funding"]}</p>')
        html.append(f'<div class="source-note">{f["source"]}</div></div>')
    html.append('</div>')
    # Nuclear timeline chart
    html.append(f'<div class="chart-row"><div class="chart-container full-width"><h3>{nc.get("title","")}</h3><canvas id="chart-nuclear-timeline"></canvas><div class="source-note">{nc.get("source","")}</div></div></div>')
    # HALEU
    haleu_link = f'<a href="{haleu.get("report","")}" style="color:var(--accent-blue);text-decoration:none;border-bottom:1px dashed var(--accent-blue)">Centrus Energy (LEU) Report &rarr;</a>'
    html.append(f'<div class="info-card" style="margin-bottom:var(--gap)"><h4>{haleu.get("title","")} &mdash; {haleu_link}</h4><p>{haleu.get("description","")}</p></div>')
    html.append('</div>')

    # ── TAB: Risks ──
    html.append('<div class="tab-content" id="tab-risks">')
    html.append('<div class="section-divider">Key Risk Factors &amp; Supply Chain Bottlenecks</div>')
    html.append('<div class="info-grid">')
    for r in risks:
        sev = r.get("severity","medium")
        html.append(f'<div class="info-card"><h4><span class="risk-indicator risk-{sev}"></span> {r["title"]}</h4>')
        html.append(f'<p><strong>Severity: {"Critical" if sev=="high" else "Medium" if sev=="medium" else "Low"}.</strong> {r["description"]}</p>')
        if r.get("impact"):
            html.append(f'<p><strong>Impact:</strong> {r["impact"]}</p>')
        if r.get("mitigation"):
            html.append(f'<p><strong>Mitigation:</strong> {r["mitigation"]}</p>')
        html.append(f'<div class="source-note">{r.get("source","")}</div></div>')
    html.append('</div>')
    sgc = charts.get("supply_demand_gap",{})
    html.append(f'<div class="chart-row"><div class="chart-container full-width"><h3>{sgc.get("title","")}</h3><canvas id="chart-gap"></canvas><div class="source-note">{sgc.get("source","")}</div></div></div>')
    html.append('</div>')

    # ── TAB: Morning News ──
    html.append('<div class="tab-content" id="tab-morningnews">')
    html.append('<div style="margin-bottom:var(--gap)"><h2 style="font-size:18px;font-weight:700;color:var(--text-on-dark);margin-bottom:8px">AI Morning News Archive</h2>')
    html.append('<p style="font-size:13px;color:var(--text-secondary)">Daily intelligence briefs covering energy, hardware, software, policy, integration &amp; financing. Click any date to open the full report.</p></div>')
    html.append('<div class="table-section"><table class="data-table" id="news-archive-table"><thead><tr><th>Date</th><th>Top Headlines</th><th>Sectors</th><th>Key Tickers</th><th>Signals</th></tr></thead><tbody>')
    for nb in sorted(briefs, key=lambda x: x.get("date",""), reverse=True):
        file_path = nb.get("file","")
        sectors_html = " ".join([f'<span class="badge badge-grid">{s}</span>' for s in nb.get("sectors",[])])
        tickers_html = ""
        for t in nb.get("tickers",[]):
            d = t.get("direction","neutral")
            color = "var(--accent-green)" if d=="up" else "var(--accent-red)" if d=="down" else "var(--accent-blue)"
            bg = "rgba(52,168,83,0.1)" if d=="up" else "rgba(234,67,53,0.1)" if d=="down" else "rgba(76,139,245,0.1)"
            note = f' {t.get("note","")}' if t.get("note") else ""
            tickers_html += f'<span style="font-size:11px;color:{color};font-weight:600;background:{bg};padding:1px 5px;border-radius:4px;margin-right:3px">{t["ticker"]}{note}</span>'
        signals_html = ""
        for s in nb.get("signals",[]):
            sig = s.get("signal","")
            if "undervalued" in sig:
                signals_html += f'<span style="display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:500;background:rgba(52,168,83,0.15);color:#34A853">{s["ticker"]} {sig}</span> '
            else:
                signals_html += f'<span style="display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:500;background:rgba(234,67,53,0.15);color:#EA4335">{s["ticker"]} {sig}</span> '
        date_display = nb.get("date","")
        html.append(f'<tr onclick="window.open(\'{file_path}\',\'_blank\')" style="cursor:pointer"><td style="white-space:nowrap;font-weight:600;color:var(--accent-blue)">{date_display}</td><td>{nb.get("top_headlines","")}</td><td>{sectors_html}</td><td>{tickers_html}</td><td>{signals_html}</td></tr>')
    html.append('</tbody></table></div>')
    html.append('<div style="font-size:12px;color:var(--text-secondary);margin-top:8px"><em>New briefs are added each morning. Click any row to open the full report.</em></div></div>')

    # Footer
    html.append(f'''<footer class="dashboard-footer">
{meta.get("title","")} Dashboard &bull; Last updated: {meta.get("last_updated","")} &bull;
{meta.get("sources","")}
<br>5 Categories: AI Software | Hyperscalers | Electricity Infrastructure | Datacenter Hardware | Semiconductor Fabrication
<br>Note: All forward-looking figures are estimates based on company guidance and analyst projections. Not investment advice.
</footer></div>''')

    # ── JavaScript ──
    html.append('<script>')
    html.append(generate_js(charts, buildouts, companies))
    html.append('</script></body></html>')

    output = "\n".join(html)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"Dashboard written to {OUT_PATH} ({len(output):,} bytes)")


def generate_js(charts, buildouts, companies):
    js = []
    js.append("""
const COLORS=['#4C8BF5','#EA4335','#F9AB00','#34A853','#A142F4','#24C1E0','#E8548C','#1DB9A0','#FF6D01','#9E9E9E'];
function switchTab(tabId){
  document.querySelectorAll('.tab-content').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  const el=document.getElementById('tab-'+tabId);
  if(el)el.classList.add('active');
  event.target.classList.add('active');
}
function filterSector(val){
  if(val==='all'){switchTab('overview');return}
  const tabMap={software:'software',hyperscaler:'hyperscaler',electricity:'electricity',dc_hardware:'dc_hardware',semiconductor_fab:'semiconductor_fab'};
  if(tabMap[val]){
    document.querySelectorAll('.tab-content').forEach(t=>t.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
    const el=document.getElementById('tab-'+tabMap[val]);
    if(el)el.classList.add('active');
  }
}
function filterRating(val){
  document.querySelectorAll('.data-table tbody tr').forEach(row=>{
    if(val==='all'){row.style.display='';return}
    const ratingCell=row.querySelector('.rating-'+val.toLowerCase());
    const isSeparator=row.querySelector('td[colspan]');
    if(isSeparator){row.style.display='';return}
    row.style.display=ratingCell?'':'none';
  });
}
function sortTableBy(tableId,colIdx){const table=document.getElementById(tableId);if(!table)return;const tbody=table.querySelector('tbody');const rows=Array.from(tbody.querySelectorAll('tr:not([data-separator])'));const dir=table.dataset.sortDir==='asc'?'desc':'asc';table.dataset.sortDir=dir;rows.sort((a,b)=>{let aVal=a.cells[colIdx].textContent.replace(/[^0-9.\\-]/g,'');let bVal=b.cells[colIdx].textContent.replace(/[^0-9.\\-]/g,'');const aNum=parseFloat(aVal),bNum=parseFloat(bVal);if(!isNaN(aNum)&&!isNaN(bNum))return dir==='asc'?aNum-bNum:bNum-aNum;aVal=a.cells[colIdx].textContent.trim();bVal=b.cells[colIdx].textContent.trim();return dir==='asc'?aVal.localeCompare(bVal):bVal.localeCompare(aVal)});rows.forEach(r=>tbody.appendChild(r))}
Chart.defaults.color='#9aa0a6';Chart.defaults.borderColor='#2d3140';Chart.defaults.font.family="-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif";
""")

    # Chart helper
    def chart_js(canvas_id, cfg):
        ctype = cfg.get("type","bar")
        if ctype in ("line","bar") and "datasets" in cfg:
            datasets = []
            for ds in cfg["datasets"]:
                d = {"label": ds["label"], "data": ds["data"], "borderColor": ds["color"], "backgroundColor": ds["color"]+"20"}
                if ds.get("fill"): d["backgroundColor"] = ds["color"]+"20"; d["fill"] = True
                if ds.get("tension"): d["tension"] = ds["tension"]
                if ds.get("borderDash"): d["borderDash"] = ds["borderDash"]
                if ds.get("borderWidth"): d["borderWidth"] = ds["borderWidth"]
                if ctype == "bar": d["backgroundColor"] = ds["color"]; del d["borderColor"]
                datasets.append(d)
            data_obj = {"labels": cfg["labels"], "datasets": datasets}
            opts = {"responsive":True,"maintainAspectRatio":False}
            if cfg.get("stacked"):
                opts["scales"] = {"x":{"stacked":True},"y":{"stacked":True,"grid":{"display":False}}}
                if cfg.get("x_title"): opts["scales"]["x"]["title"] = {"display":True,"text":cfg["x_title"]}
            else:
                opts["interaction"] = {"mode":"index","intersect":False}
                opts["plugins"] = {"legend":{"position":"top","labels":{"usePointStyle":True,"padding":15}}}
                scales = {}
                if cfg.get("y_begin_zero"): scales["y"] = {"beginAtZero":True}
                if cfg.get("y_title"): scales.setdefault("y",{})["title"] = {"display":True,"text":cfg["y_title"]}
                if cfg.get("x_title"): scales["x"] = {"title":{"display":True,"text":cfg["x_title"]}}
                scales.setdefault("x",{})["grid"] = {"display":False}
                if cfg.get("x_min"): scales["x"]["min"] = cfg["x_min"]
                if cfg.get("x_max"): scales["x"]["max"] = cfg["x_max"]
                opts["scales"] = scales
            if cfg.get("indexAxis"): opts["indexAxis"] = cfg["indexAxis"]
            return f"new Chart(document.getElementById('{canvas_id}'),{{type:'{ctype}',data:{json.dumps(data_obj)},options:{json.dumps(opts)}}});"
        elif ctype == "doughnut":
            colors = cfg.get("colors",[])
            data_obj = {"labels":cfg["labels"],"datasets":[{"data":cfg["data"],"backgroundColor":colors,"borderColor":"#1a1d28","borderWidth":3}]}
            opts = {"responsive":True,"maintainAspectRatio":False,"cutout":cfg.get("cutout","55%"),"plugins":{"legend":{"position":"right","labels":{"usePointStyle":True,"padding":12,"font":{"size":12}}}}}
            return f"new Chart(document.getElementById('{canvas_id}'),{{type:'doughnut',data:{json.dumps(data_obj)},options:{json.dumps(opts)}}});"
        elif ctype == "bar" and "data" in cfg and "labels" in cfg:
            colors = cfg.get("colors",[])
            data_obj = {"labels":cfg["labels"],"datasets":[{"label":cfg.get("title",""),"data":cfg["data"],"backgroundColor":colors,"borderRadius":6}]}
            opts = {"responsive":True,"maintainAspectRatio":False,"plugins":{"legend":{"display":False}}}
            scales = {}
            if cfg.get("y_title"): scales["y"] = {"beginAtZero":True,"title":{"display":True,"text":cfg["y_title"]}}
            if cfg.get("x_title"): scales["x"] = {"beginAtZero":True,"title":{"display":True,"text":cfg["x_title"]}}
            scales.setdefault("x" if cfg.get("indexAxis")=="y" else "y",{})
            if not cfg.get("indexAxis"): scales.setdefault("x",{})["grid"] = {"display":False}
            else: scales.setdefault("y",{})["grid"] = {"display":False}
            opts["scales"] = scales
            if cfg.get("indexAxis"): opts["indexAxis"] = cfg["indexAxis"]
            return f"new Chart(document.getElementById('{canvas_id}'),{{type:'bar',data:{json.dumps(data_obj)},options:{json.dumps(opts)}}});"
        return ""

    # Standard charts from chart_data
    chart_map = {
        "demand_projections": "chart-demand",
        "energy_mix": "chart-energymix",
        "clean_energy": "chart-cleanenergy",
        "power_timeline": "chart-timeline",
        "turbine_backlog": "chart-turbine-backlog",
        "nuclear_ppas": "chart-nuclear-ppas",
        "sic_market": "chart-sic",
        "lead_times": "chart-leadtimes",
        "nuclear_timeline": "chart-nuclear-timeline",
        "supply_demand_gap": "chart-gap",
    }
    for chart_id, canvas_id in chart_map.items():
        cfg = charts.get(chart_id, {})
        if cfg:
            js.append(chart_js(canvas_id, cfg))

    # Sector distribution doughnut
    from collections import Counter
    sector_counts = Counter(c["sector"] for c in companies)
    sector_labels = ["AI Software","Hyperscalers","Electricity","DC Hardware","Semicond Fab"]
    sector_keys = ["software","hyperscaler","electricity","dc_hardware","semiconductor_fab"]
    sector_data = [sector_counts.get(k,0) for k in sector_keys]
    sector_colors = ["#A142F4","#4C8BF5","#F9AB00","#34A853","#EA4335"]
    sector_dist = {"labels":sector_labels,"datasets":[{"data":sector_data,"backgroundColor":sector_colors,"borderColor":"#1a1d28","borderWidth":3}]}
    js.append(f"new Chart(document.getElementById('chart-sector-dist'),{{type:'doughnut',data:{json.dumps(sector_dist)},options:{{responsive:true,maintainAspectRatio:false,cutout:'55%',plugins:{{legend:{{position:'right',labels:{{usePointStyle:true,padding:12,font:{{size:12}}}}}}}}}}}});")

    # Rating distribution
    rating_counts = Counter(c.get("rating","Unrated") or "Unrated" for c in companies)
    rat_labels = ["Strong Buy","Buy","Hold","Sell","Unrated"]
    rat_keys = ["STRONG_BUY","BUY","HOLD","SELL","Unrated"]
    rat_data = [rating_counts.get(k,0) for k in rat_keys]
    rat_colors = ["#34A853","#4C8BF5","#F9AB00","#EA4335","#9E9E9E"]
    rat_dist = {"labels":rat_labels,"datasets":[{"data":rat_data,"backgroundColor":rat_colors,"borderColor":"#1a1d28","borderWidth":3}]}
    js.append(f"new Chart(document.getElementById('chart-rating-dist'),{{type:'doughnut',data:{json.dumps(rat_dist)},options:{{responsive:true,maintainAspectRatio:false,cutout:'55%',plugins:{{legend:{{position:'right',labels:{{usePointStyle:true,padding:12,font:{{size:12}}}}}}}}}}}});")

    # CapEx from buildout data
    if buildouts:
        names = [b["name"] for b in buildouts]
        d24 = [b.get("capex_2024",0) for b in buildouts]
        d25 = [b.get("capex_2025",0) for b in buildouts]
        d26 = [b.get("capex_2026e",0) for b in buildouts]
        capex_data = {"labels":names,"datasets":[
            {"label":"2024 Actual","data":d24,"backgroundColor":"#9E9E9E80"},
            {"label":"2025 Actual","data":d25,"backgroundColor":"#4C8BF5CC"},
            {"label":"2026 Estimate","data":d26,"backgroundColor":"#F9AB00CC"}
        ]}
        capex_opts = {"responsive":True,"maintainAspectRatio":False,"plugins":{"legend":{"position":"top","labels":{"usePointStyle":True,"padding":15}}},"scales":{"y":{"beginAtZero":True,"title":{"display":True,"text":"Capital Expenditure ($B)"}},"x":{"grid":{"display":False}}}}
        js.append("new Chart(document.getElementById('chart-capex'),{type:'bar',data:" + json.dumps(capex_data) + ",options:" + json.dumps(capex_opts) + "});")

        # Power capacity
        current_gw = [b.get("chart_current_gw",0) for b in buildouts]
        target_gw = [b.get("chart_target_gw",0) for b in buildouts]
        power_data = {"labels":names,"datasets":[
            {"label":"Current / Active (GW)","data":current_gw,"backgroundColor":"#4C8BF5CC"},
            {"label":"Target (GW)","data":target_gw,"backgroundColor":"#F9AB0080"}
        ]}
        power_opts = {"responsive":True,"maintainAspectRatio":False,"plugins":{"legend":{"position":"top","labels":{"usePointStyle":True}}},"scales":{"y":{"beginAtZero":True,"title":{"display":True,"text":"GW"}},"x":{"grid":{"display":False}}}}
        js.append("new Chart(document.getElementById('chart-hscaler-power'),{type:'bar',data:" + json.dumps(power_data) + ",options:" + json.dumps(power_opts) + "});")

        # CapEx 25 vs 26
        capex2_data = {"labels":names,"datasets":[
            {"label":"2025 ($B)","data":d25,"backgroundColor":"#4C8BF5AA"},
            {"label":"2026E ($B)","data":d26,"backgroundColor":"#F9AB00AA"}
        ]}
        capex2_opts = {"responsive":True,"maintainAspectRatio":False,"plugins":{"legend":{"position":"top","labels":{"usePointStyle":True}}},"scales":{"y":{"beginAtZero":True,"title":{"display":True,"text":"$B"}},"x":{"grid":{"display":False}}}}
        js.append("new Chart(document.getElementById('chart-hscaler-capex'),{type:'bar',data:" + json.dumps(capex2_data) + ",options:" + json.dumps(capex2_opts) + "});")

    # Live Financial Data Fetching
    js.append("""
(function(){
  var WORKER_URL = window.FINANCE_WORKER_URL || '';
  var REFRESH_INTERVAL = 15 * 60 * 1000;

  var statusEl = document.createElement('div');
  statusEl.className = 'live-status';
  statusEl.innerHTML = '<span class="dot loading"></span> Loading live data...';
  document.body.appendChild(statusEl);

  function showStatus(msg, state){
    var dot = statusEl.querySelector('.dot');
    dot.className = 'dot ' + state;
    dot.nextSibling.textContent = ' ' + msg;
    if(state === 'ok'){
      setTimeout(function(){ statusEl.style.opacity='0'; }, 4000);
      setTimeout(function(){ statusEl.style.display='none'; }, 4500);
    }
  }

  function collectTickers(){
    var tickers = [];
    var seen = {};
    document.querySelectorAll('tr[data-ticker]').forEach(function(row){
      var t = row.getAttribute('data-ticker');
      if(t && t.length > 0 && t.length < 10 && !seen[t]){
        tickers.push(t);
        seen[t] = true;
      }
    });
    return tickers;
  }

  function fmtPrice(v){ return v != null ? '$' + Number(v).toFixed(2) : String.fromCharCode(8212); }
  function fmtChange(v){
    if(v == null) return String.fromCharCode(8212);
    var n = Number(v);
    var sign = n >= 0 ? '+' : '';
    return sign + n.toFixed(2) + '%';
  }
  function fmtMcap(v){
    if(v == null) return String.fromCharCode(8212);
    var n = Number(v);
    if(n >= 1e12) return '$' + (n/1e12).toFixed(2) + 'T';
    if(n >= 1e9) return '$' + (n/1e9).toFixed(1) + 'B';
    if(n >= 1e6) return '$' + (n/1e6).toFixed(0) + 'M';
    return '$' + n.toLocaleString();
  }
  function fmtPE(v){ return v != null && v > 0 ? Number(v).toFixed(1) + 'x' : String.fromCharCode(8212); }

  function populateRow(row, quote){
    var fields = {
      'price': fmtPrice(quote.price),
      'change': fmtChange(quote.changesPercentage),
      'mktCap': fmtMcap(quote.marketCap),
      'pe': fmtPE(quote.pe)
    };
    Object.keys(fields).forEach(function(field){
      var cell = row.querySelector('[data-field="' + field + '"]');
      if(cell){
        cell.textContent = fields[field];
        cell.classList.remove('live-loading');
        if(field === 'change' && quote.changesPercentage != null){
          cell.classList.remove('positive','negative');
          cell.classList.add(quote.changesPercentage >= 0 ? 'positive' : 'negative');
        }
      }
    });
  }

  function setLoading(){
    document.querySelectorAll('[data-field]').forEach(function(cell){
      if(cell.textContent === String.fromCharCode(8212) || cell.classList.contains('live-loading')){
        cell.textContent = String.fromCharCode(8230);
        cell.classList.add('live-loading');
      }
    });
  }

  function fetchLiveData(){
    if(!WORKER_URL){
      showStatus('No API configured', 'err');
      return;
    }
    var tickers = collectTickers();
    if(tickers.length === 0){ showStatus('No tickers found', 'err'); return; }

    setLoading();
    showStatus('Fetching ' + tickers.length + ' quotes...', 'loading');

    var chunks = [];
    for(var i = 0; i < tickers.length; i += 30){
      chunks.push(tickers.slice(i, i + 30));
    }

    var allQuotes = [];
    var pending = chunks.length;

    chunks.forEach(function(chunk){
      var url = WORKER_URL + '/quotes?symbols=' + chunk.join(',');
      fetch(url).then(function(resp){
        if(!resp.ok) throw new Error('HTTP ' + resp.status);
        return resp.json();
      }).then(function(data){
        if(Array.isArray(data)) allQuotes = allQuotes.concat(data);
        pending--;
        if(pending === 0) applyQuotes(allQuotes, tickers.length);
      }).catch(function(err){
        console.error('Live data fetch error:', err);
        pending--;
        if(pending === 0) applyQuotes(allQuotes, tickers.length);
      });
    });
  }

  function applyQuotes(allQuotes, totalTickers){
    var bySymbol = {};
    allQuotes.forEach(function(q){ if(q.symbol) bySymbol[q.symbol] = q; });
    document.querySelectorAll('tr[data-ticker]').forEach(function(row){
      var ticker = row.getAttribute('data-ticker');
      if(bySymbol[ticker]) populateRow(row, bySymbol[ticker]);
    });
    var count = Object.keys(bySymbol).length;
    if(count > 0){
      showStatus(count + '/' + totalTickers + ' quotes loaded', 'ok');
    } else {
      showStatus('No quotes returned', 'err');
      document.querySelectorAll('.live-loading').forEach(function(cell){
        cell.textContent = String.fromCharCode(8212);
        cell.classList.remove('live-loading');
      });
    }
  }

  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', function(){ fetchLiveData(); });
  } else {
    fetchLiveData();
  }
  setInterval(fetchLiveData, REFRESH_INTERVAL);
  window.refreshLiveData = fetchLiveData;
})();
""")

    return "\n".join(js)

if __name__ == "__main__":
    generate()
