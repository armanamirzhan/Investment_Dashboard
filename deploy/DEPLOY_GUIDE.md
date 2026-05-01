# Deployment Guide — lumentel.com/invest

## Architecture

```
lumentel.com (existing Cloudflare Pages site)
├── invest/                  ← Static dashboard files (this folder goes into your GitHub repo)
│   ├── index.html           ← Main dashboard
│   ���── morning-news/*.html  ← Daily news briefs
│   └── reports/*.html       ← Individual company reports
└── (rest of your existing site)

finance-proxy (Cloudflare Worker)
└── worker.js                ← API proxy for FMP live stock data
```

## Step-by-Step Setup

### 1. Add invest/ to your GitHub repo

Copy the `invest/` folder into the root of your `lumentel.com` GitHub repo:

```bash
cp -r invest/ /path/to/lumentel-repo/invest/
cd /path/to/lumentel-repo
git add invest/
git commit -m "Add investment dashboard"
git push
```

Cloudflare Pages will auto-deploy. Visit `lumentel.com/invest` to verify.

### 2. Deploy the Cloudflare Worker (for live stock data)

```bash
cd deploy/worker
npm install -g wrangler          # if not already installed
wrangler login                   # authenticate with Cloudflare
wrangler secret put FMP_API_KEY  # paste your FMP API key when prompted
wrangler deploy                  # deploys to finance-proxy.<subdomain>.workers.dev
```

### 3. Connect live data to dashboard

After deploying the Worker, note its URL (e.g., `https://finance-proxy.your-subdomain.workers.dev`).

Edit `scripts/generate_dashboard.py` and find the live data section. Set:
```javascript
window.FINANCE_WORKER_URL = 'https://finance-proxy.your-subdomain.workers.dev';
```

Or optionally, route through your domain by uncommenting the route in `wrangler.toml`:
```toml
routes = [{ pattern = "lumentel.com/api/finance/*", zone_name = "lumentel.com" }]
```

Then regenerate and redeploy:
```bash
python scripts/generate_dashboard.py
python scripts/deploy_invest.py
cd /path/to/lumentel-repo && git add invest/ && git commit -m "Update dashboard" && git push
```

### 4. Daily updates (automated)

The scheduled task "Morning AI news" runs daily and:
1. Researches latest AI/datacenter news
2. Updates JSON data files (additive, preserves history)
3. Regenerates dashboard + news HTML
4. Runs `deploy_invest.py` to copy to invest/
5. Pushes to GitHub (triggering Cloudflare Pages rebuild)

## Free Tier Limits

- **Cloudflare Pages**: Unlimited sites, 500 builds/month
- **Cloudflare Workers**: 100K requests/day free
- **FMP API**: 250 requests/day free (Worker caches for 15 min)
