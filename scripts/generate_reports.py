#!/usr/bin/env python3
"""Generate individual company report HTML files from JSON data."""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_init import load, today

# Matches the kpi-row block (8 KPI cards) up to the next <div class="section">.
KPI_BLOCK_RE = re.compile(r'<div class="kpi-row">.*?</div></div>(?=<div class="section">)', re.DOTALL)


def splice_kpi_block(existing_html, new_html):
    """Replace the kpi-row block in existing_html with the one from new_html.
    Returns the patched HTML, or None if either side lacks the marker."""
    new_match = KPI_BLOCK_RE.search(new_html)
    if not new_match or not KPI_BLOCK_RE.search(existing_html):
        return None
    return KPI_BLOCK_RE.sub(new_match.group(0), existing_html, count=1)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

CSS = r"""
:root{--bg-primary:#0f1117;--bg-card:#1a1d28;--bg-hover:#252836;--text-primary:#e8eaed;--text-secondary:#9aa0a6;--text-on-dark:#ffffff;--border:#2d3140;--accent-blue:#4C8BF5;--accent-green:#34A853;--accent-orange:#F9AB00;--accent-red:#EA4335;--accent-purple:#A142F4;--gap:16px;--radius:10px}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg-primary);color:var(--text-primary);line-height:1.6}
.container{max-width:1000px;margin:0 auto;padding:var(--gap)}
.back-link{display:inline-block;margin-bottom:var(--gap);color:var(--accent-blue);text-decoration:none;font-size:13px}
.back-link:hover{text-decoration:underline}
.header{background:linear-gradient(135deg,#1a1d28,#0f1117);border:1px solid var(--border);padding:28px 32px;border-radius:var(--radius);margin-bottom:var(--gap);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px}
.header h1{font-size:24px;font-weight:700;color:var(--text-on-dark)}
.header .ticker{font-size:14px;padding:4px 12px;border-radius:6px;background:rgba(76,139,245,0.15);color:var(--accent-blue);font-weight:700}
.header .rating{font-size:18px}
.kpi-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:var(--gap);margin-bottom:var(--gap)}
.kpi-card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);padding:16px 20px;text-align:center}
.kpi-label{font-size:10px;color:var(--text-secondary);text-transform:uppercase;letter-spacing:0.8px;margin-bottom:4px}
.kpi-value{font-size:20px;font-weight:700;color:var(--text-on-dark)}
.section{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);padding:20px 24px;margin-bottom:var(--gap)}
.section h3{font-size:14px;font-weight:600;margin-bottom:12px;color:var(--accent-blue)}
.section p{font-size:13px;color:var(--text-secondary);margin-bottom:8px}
.staleness-badge{display:inline-block;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600;margin-left:12px}
.stale-fresh{background:rgba(52,168,83,0.15);color:#34A853}
.stale-aging{background:rgba(249,171,0,0.15);color:#F9AB00}
.stale-old{background:rgba(234,67,53,0.15);color:#EA4335}
.source-note{font-size:11px;color:var(--text-secondary);margin-top:12px;padding-top:8px;border-top:1px solid var(--border)}
footer{text-align:center;padding:16px;color:var(--text-secondary);font-size:11px;border-top:1px solid var(--border);margin-top:24px}
"""

def staleness_badge(updated_date):
    """Return a staleness badge based on how old the data is."""
    from datetime import date, datetime
    if not updated_date:
        return '<span class="staleness-badge stale-old">No date</span>'
    try:
        upd = datetime.strptime(updated_date, "%Y-%m-%d").date()
        delta = (date.today() - upd).days
        if delta <= 3:
            return f'<span class="staleness-badge stale-fresh">Updated {delta}d ago</span>'
        elif delta <= 14:
            return f'<span class="staleness-badge stale-aging">Updated {delta}d ago</span>'
        else:
            return f'<span class="staleness-badge stale-old">Stale ({delta}d)</span>'
    except:
        return '<span class="staleness-badge stale-aging">Unknown date</span>'

def generate_report(company_data, financials_data=None):
    """Generate a single company report HTML."""
    ticker = company_data["ticker"]
    name = company_data["name"]
    rating = company_data.get("rating","")
    emoji = company_data.get("emoji","")
    report_file = company_data.get("report")
    if not report_file:
        return None

    updated = company_data.get("updated", "")
    stale = staleness_badge(updated)

    fin = {}
    if financials_data:
        ticker_fins = [f for f in financials_data if f.get("ticker") == ticker]
        if ticker_fins:
            fin = ticker_fins[-1]

    rating_map = {"STRONG_BUY":"Strong Buy","BUY":"Buy","HOLD":"Hold","SELL":"Sell/Avoid"}
    rating_label = rating_map.get(rating, rating or "N/A")

    html = f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name} ({ticker}) - Investment Report</title>
<style>{CSS}</style></head><body>
<div class="container">
<a href="../AI_Datacenter_Power_Landscape.html" class="back-link">&larr; Back to Dashboard</a>
<div class="header">
<div><h1>{emoji} {name}</h1></div>
<div style="display:flex;align-items:center;gap:12px">
<span class="ticker">{ticker}</span>
<span class="rating">{rating_label}</span>
{stale}
</div></div>
<div class="kpi-row">'''

    kpi_fields = [
        ("market_cap", "Market Cap", lambda v: f"${v/1e9:.0f}B" if v and v > 1e6 else "N/A"),
        ("stock_price", "Stock Price", lambda v: f"${v:.2f}" if v else "N/A"),
        ("pe_ratio", "P/E Ratio", lambda v: f"{v:.1f}x" if v else "N/A"),
        ("revenue", "Revenue (TTM)", lambda v: f"${v/1e9:.1f}B" if v and v > 1e6 else "N/A"),
        ("revenue_growth", "Rev Growth", lambda v: f"{v:.1f}%" if v else "N/A"),
        ("operating_margin", "Op Margin", lambda v: f"{v:.1f}%" if v else "N/A"),
        ("ev_ebitda", "EV/EBITDA", lambda v: f"{v:.1f}x" if v else "N/A"),
        ("debt_to_equity", "D/E Ratio", lambda v: f"{v:.2f}" if v else "N/A"),
    ]
    for field, label, fmt in kpi_fields:
        val = fin.get(field)
        html += f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-value">{fmt(val)}</div></div>'

    html += '</div>'

    html += f'''<div class="section">
<h3>Company Profile</h3>
<p><strong>Sector:</strong> {company_data.get("sector","").replace("_"," ").title()}</p>
<p><strong>Sub-sector:</strong> {company_data.get("sub_sector","N/A")}</p>
<p><strong>DC Revenue Exposure:</strong> {company_data.get("exposure","N/A")}</p>
<p><strong>Rating:</strong> {emoji} {rating_label}</p>
</div>'''

    thesis = company_data.get("thesis","")
    if thesis:
        html += f'<div class="section"><h3>Investment Thesis</h3><p>{thesis}</p></div>'

    catalysts = company_data.get("catalysts",[])
    if catalysts:
        html += '<div class="section"><h3>Growth Catalysts</h3>'
        for cat in catalysts:
            html += f'<p>&bull; {cat}</p>'
        html += '</div>'

    co_risks = company_data.get("risks",[])
    if co_risks:
        html += '<div class="section"><h3>Risks &amp; Concerns</h3>'
        for r in co_risks:
            html += f'<p>&bull; {r}</p>'
        html += '</div>'

    sources = company_data.get("sources",[])
    if sources:
        html += '<div class="section"><h3>Sources</h3>'
        for s in sources:
            if isinstance(s, dict):
                html += f'<p><a href="{s.get("url","#")}" style="color:var(--accent-blue)">{s.get("name","Source")}</a></p>'
            else:
                html += f'<p>{s}</p>'
        html += '</div>'

    html += f'''<footer>{name} ({ticker}) - Investment Report &bull; Data as of {updated or "N/A"} &bull; Not investment advice.</footer>
</div></body></html>'''

    # Write — but don't overwrite existing files that are richer.
    # report_file may be stored as "reports/X.html" (for dashboard links) or just "X.html".
    os.makedirs(REPORTS_DIR, exist_ok=True)
    out_path = os.path.join(REPORTS_DIR, os.path.basename(report_file))
    new_size = len(html.encode("utf-8"))

    if os.path.exists(out_path):
        existing_size = os.path.getsize(out_path)
        if existing_size > new_size and "--force" not in sys.argv:
            with open(out_path, "r", encoding="utf-8") as fh:
                existing = fh.read()
            patched = splice_kpi_block(existing, html)
            if patched and patched != existing:
                with open(out_path, "w", encoding="utf-8") as fh:
                    fh.write(patched)
                print(f"  PATCHED {report_file}: KPI block refreshed")
                return out_path
            print(f"  SKIP {report_file}: existing {existing_size}B > generated {new_size}B (no KPI marker)")
            return out_path

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  WROTE {report_file}: {new_size}B")
    return out_path

def generate_all():
    """Generate reports for all companies. Skips richer existing files unless --force."""
    companies = load("companies", [])
    financials = load("financials", [])
    count = 0
    for co in companies:
        if co.get("report"):
            path = generate_report(co, financials)
            if path:
                count += 1
    print(f"Processed {count} company reports in {REPORTS_DIR}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != "--force":
        ticker = sys.argv[1].upper()
        companies = load("companies", [])
        for co in companies:
            if co["ticker"] == ticker:
                path = generate_report(co, load("financials",[]))
                if path:
                    print(f"Report written: {path}")
                break
    else:
        generate_all()
