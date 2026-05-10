# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture

Static-site investment dashboard. JSON files in `data/` are the **single source of truth**; Python generators in `scripts/` read JSON and emit standalone HTML. There is no server, build tool, framework, or database — just Python stdlib + plain HTML/JS (Chart.js loaded via CDN inside the generated pages).

### Data flow

```
data/*.json  →  scripts/generate_*.py  →  HTML (root, reports/, morning-news/)  →  scripts/deploy_invest.py  →  invest/
```

Three independent generators, each producing different artifacts:

- [scripts/generate_dashboard.py](scripts/generate_dashboard.py) → [AI_Datacenter_Power_Landscape.html](AI_Datacenter_Power_Landscape.html) (the main dashboard)
- [scripts/generate_reports.py](scripts/generate_reports.py) → one HTML per company in [reports/](reports/), driven by `companies.json` entries that have a `report` field
- [scripts/generate_news.py](scripts/generate_news.py) → daily brief in [morning-news/YYYY-MM-DD.html](morning-news/), reading `news_entries_<date>.json`

[scripts/db_init.py](scripts/db_init.py) is the JSON load/save helper used by every other script (`load(name)` / `save(name, data)` map name → `data/<name>.json`). All scripts add the `scripts/` dir to `sys.path` and import from `db_init`. There is no package; do not introduce one.

[scripts/update_data.py](scripts/update_data.py) is the **mutation API** intended to be called by scheduled research tasks — small functions like `update_kpi`, `add_company`, `add_financials`, `add_analyst_change`, `add_news_entry`. After mutating data, call `regenerate_all()` (or `python scripts/update_data.py regenerate`) to rebuild every HTML file.

[scripts/fetch_prices.py](scripts/fetch_prices.py) pulls live market data (price, market cap, P/E, P/S, EV/EBITDA, revenue, growth, margins, D/E, analyst target, day change %, Wall Street consensus rating, analyst count, upside %) from yfinance for every public ticker in `companies.json`, writes via `add_financials` + `add_valuation_snapshot`, then calls `regenerate_all()`. Money-denominated values (price, market cap, revenue, analyst target) are converted to USD via yfinance FX pairs (`KRWUSD=X` etc.) using `info["currency"]`; the FX rate is cached per run. Native currency is preserved on each financials entry as `currency_native`.

### Three rating signals

The dashboard's company tables show three independent rating columns, each from a different source:

- **House Rating** (column "Rating") — editorial, hand-set in `companies.json` per company. Not model-driven. Values: `STRONG_BUY` / `BUY` / `HOLD` / `SELL` (uppercase canonical enums; render via `rating_html()` in `generate_dashboard.py`).
- **Wall St** — Yahoo Finance analyst consensus, populated client-side from `wallstreet_rating` + `wallstreet_count` + `wallstreet_mean` in `financials.json` (yfinance `recommendationKey` / `numberOfAnalystOpinions` / `recommendationMean`).
- **Upside** — implied % to consensus 12-month price target, from `upside_pct` in `financials.json` (yfinance `targetMeanPrice` ÷ `currentPrice`).

All three column headers and the Rating cell are clickable and switch the dashboard to the **Methodology** tab (rendered in `generate_dashboard.py` under `tab-methodology`), which documents each signal. The House Rating methodology section is a placeholder meant to be edited to match the actual editorial rubric.

[.github/workflows/refresh.yml](.github/workflows/refresh.yml) runs `fetch_prices.py` hourly during US market hours (Mon-Fri 14:00-21:00 UTC) and on manual dispatch, then runs `deploy_invest.py` and commits the updated `data/`, regenerated HTML, and the `invest/` artifact back to the repo as `github-actions[bot]`. Concurrency is serialized — overlapping runs queue rather than cancel.

[.github/workflows/morning-news.yml](.github/workflows/morning-news.yml) and [.github/workflows/midday-update.yml](.github/workflows/midday-update.yml) run a Claude Code agent (via `anthropics/claude-code-action` authenticated with `CLAUDE_CODE_OAUTH_TOKEN` from the user's Claude Max subscription) on a daily schedule:
- **Pre-open** (M-F, 9 AM ET) — researches overnight news and writes news entries, analyst changes, and watchlist signals via `update_data.py`. This is the only run that calls `add_news_entry`.
- **Mid-day** (Daily, 12 PM ET) — captures intraday analyst moves and signals. Does NOT call `add_news_entry`; the morning brief is finalized by the pre-open run.

Both jobs use a DST-aware shell gate (two cron times, one TZ check) so the agent only fires once per day at the intended ET hour. Both run `regenerate_all()` inside the agent prompt and `deploy_invest.py` afterward in the workflow, then commit the same paths as `refresh.yml`.

[scripts/seed_data.py](scripts/seed_data.py) writes a hardcoded baseline of every JSON file. Treat it as a **fallback/bootstrap, not a migration** — `companies.json` and others are now edited directly and have diverged from the seed (the seed has 14 companies; live data has the full ~84). Don't run `seed_data.py` on a working dataset, it will overwrite.

[scripts/deploy_invest.py](scripts/deploy_invest.py) copies generated HTML into `invest/` for GitHub/Cloudflare Pages, renaming the dashboard to `index.html` and rewriting back-links from `../AI_Datacenter_Power_Landscape.html` → `../index.html` in the morning-news files. The `invest/` folder is the deploy artifact.

### Report generation quirk

`generate_reports.py` won't fully overwrite an existing report that's larger than the freshly-generated one. Instead it **splices the `<div class="kpi-row">` block** from the new HTML into the existing file (regex-matched, terminated by the next `<div class="section">`), keeping the hand-written narrative intact. If the existing file lacks that marker (different layout — e.g. SK Hynix, Samsung, Cisco, Vertiv, Asetek, Bloom, Plug, FuelCell), the file is skipped entirely and KPIs there will not auto-refresh until those reports are reformatted to match. Pass `--force` to bypass the size check and rewrite a report from scratch.

### Dashboard live-data flow

The dashboard HTML embeds static counts/sector charts at generation time, but pulls per-ticker KPIs (price, market cap, P/E, change %) **client-side at page load** via `fetch('data/financials.json')`. Cells start as em-dashes with `class="live-price"` / `data-field="price"` and get populated by the IIFE at the bottom of the dashboard. The fetch refreshes every 15 minutes while the tab is open. This means the deploy step must ship `data/financials.json` next to the dashboard — handled by [scripts/deploy_invest.py](scripts/deploy_invest.py).

### Sector taxonomy

Five categories everywhere (`sector` field on companies, badge classes in CSS, chart groupings): `software`, `hyperscaler`, `electricity`, `dc_hardware`, `semiconductor_fab`. The label/icon/color mapping lives in `SECTOR_META` at the top of `generate_dashboard.py`.

## Commands

All run from the repo root.

```bash
# Refresh live market data (yfinance) + regenerate
python scripts/fetch_prices.py
python scripts/fetch_prices.py --no-regen          # data only, skip HTML
python scripts/fetch_prices.py NVDA MSFT 005930.KS # specific tickers

# Regenerate everything from data/
python scripts/update_data.py regenerate

# Regenerate one artifact
python scripts/generate_dashboard.py
python scripts/generate_news.py            # today's date
python scripts/generate_news.py 2026-05-09 # specific date
python scripts/generate_reports.py         # all companies, skips larger existing files
python scripts/generate_reports.py NVDA    # single ticker
python scripts/generate_reports.py --force # overwrite all

# Stage for deploy
python scripts/deploy_invest.py            # copies into invest/

# Inspect data
python scripts/db_init.py                  # prints DATA_DIR + lists json files
```

There are no tests, no linter config, and no `requirements.txt`. Third-party deps (`requests`, `yfinance`) are installed by [.devcontainer/devcontainer.json](.devcontainer/devcontainer.json) `postCreateCommand` on Codespace build.

## Preview

The devcontainer forwards port 5500 for the Live Server VS Code extension. Right-click any `.html` file → "Open with Live Server" to preview.

## When editing

- Edit JSON in `data/` then run a generator — never edit the generated HTML directly (it gets overwritten). The exception is hand-enriched files in `reports/` that the size guard preserves.
- The four `*.md` files at the repo root (`AI_Software_Companies_Investment_Landscape.md` etc.) are **research notes, not generated**. They're sector writeups maintained by hand and not consumed by any script.
- CSS lives as a multi-line string constant at the top of each generator. Each generator has its own `CSS` — they share design tokens (`--bg-primary`, `--accent-blue`, etc.) but are not deduplicated.
- Dates: `db_init.today()` returns `date.today().isoformat()`. News entries are stored per-day under `news_entries_<YYYY-MM-DD>.json`, not appended to a single file.

## Working style

- **Never assume, never act on incomplete information.** If anything about the request, the data, or the intended behavior is unclear or ambiguous, stop and ask the user before proceeding. Do not guess defaults, do not pick "the reasonable interpretation" silently, and do not fill gaps with plausible-sounding values. Wait for the user's answer — do not time-out the question, do not proceed with a tentative plan in parallel, and do not say "I'll assume X unless you say otherwise." Block on the answer.
- **Proactively suggest useful tooling.** When starting or scoping a task, consider whether any available addon, subagent, skill, MCP server, or plugin would improve the quality or efficiency of execution (e.g. the `Explore` subagent for broad codebase searches, the `Plan` subagent for designing multi-step changes, `/security-review` before shipping risky changes, `/review` for PR review, `simplify` for post-change cleanup, `update-config` for harness/permission tweaks, `claude-api` when touching Anthropic SDK code). Mention the suggestion briefly to the user before invoking, so they can opt in or redirect.
