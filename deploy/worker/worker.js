/**
 * Cloudflare Worker — Financial Data Proxy for AI Investment Dashboard
 * 
 * Proxies requests to Financial Modeling Prep (FMP) API.
 * Keeps the API key server-side (stored as a Worker secret).
 * Caches responses for 15 minutes to stay within free-tier limits.
 * 
 * Deploy: wrangler deploy
 * Set secret: wrangler secret put FMP_API_KEY
 * 
 * Endpoints:
 *   GET /quotes?symbols=NVDA,AMD,TSM,...    → batch stock quotes
 *   GET /profile?symbols=NVDA,AMD,...        → company profiles (market cap, sector, etc.)
 *   GET /ratios?symbol=NVDA                  → financial ratios (P/E, P/S, EV/EBITDA)
 *   GET /health                              → health check
 */

const FMP_BASE = 'https://financialmodelingprep.com/api/v3';

// CORS headers for your dashboard domain
const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',  // Tighten to 'https://lumentel.com' in production
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Access-Control-Max-Age': '86400',
};

// Cache duration in seconds (15 min keeps you well within 250 req/day free tier)
const CACHE_TTL = 900;

export default {
  async fetch(request, env, ctx) {
    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: CORS_HEADERS });
    }

    const url = new URL(request.url);
    const path = url.pathname;

    // Only allow GET
    if (request.method !== 'GET') {
      return jsonResponse({ error: 'Method not allowed' }, 405);
    }

    try {
      // Route to appropriate handler
      if (path === '/quotes' || path === '/api/finance/quotes') {
        return await handleQuotes(url, env, ctx);
      } else if (path === '/profile' || path === '/api/finance/profile') {
        return await handleProfile(url, env, ctx);
      } else if (path === '/ratios' || path === '/api/finance/ratios') {
        return await handleRatios(url, env, ctx);
      } else if (path === '/metrics' || path === '/api/finance/metrics') {
        return await handleKeyMetrics(url, env, ctx);
      } else if (path === '/health' || path === '/api/finance/health') {
        return jsonResponse({ status: 'ok', timestamp: new Date().toISOString() });
      } else {
        return jsonResponse({ error: 'Not found', endpoints: ['/quotes', '/profile', '/ratios', '/metrics', '/health'] }, 404);
      }
    } catch (err) {
      return jsonResponse({ error: 'Internal error', message: err.message }, 500);
    }
  }
};

// --- Handlers ---

async function handleQuotes(url, env, ctx) {
  const symbols = url.searchParams.get('symbols');
  if (!symbols) return jsonResponse({ error: 'Missing ?symbols= parameter' }, 400);

  // FMP batch quote endpoint
  const fmpUrl = `${FMP_BASE}/quote/${symbols}?apikey=${env.FMP_API_KEY}`;
  return await cachedFetch(fmpUrl, `quotes:${symbols}`, env, ctx);
}

async function handleProfile(url, env, ctx) {
  const symbols = url.searchParams.get('symbols');
  if (!symbols) return jsonResponse({ error: 'Missing ?symbols= parameter' }, 400);

  const fmpUrl = `${FMP_BASE}/profile/${symbols}?apikey=${env.FMP_API_KEY}`;
  return await cachedFetch(fmpUrl, `profile:${symbols}`, env, ctx);
}

async function handleRatios(url, env, ctx) {
  const symbol = url.searchParams.get('symbol');
  if (!symbol) return jsonResponse({ error: 'Missing ?symbol= parameter' }, 400);

  const fmpUrl = `${FMP_BASE}/ratios-ttm/${symbol}?apikey=${env.FMP_API_KEY}`;
  return await cachedFetch(fmpUrl, `ratios:${symbol}`, env, ctx);
}

async function handleKeyMetrics(url, env, ctx) {
  const symbol = url.searchParams.get('symbol');
  if (!symbol) return jsonResponse({ error: 'Missing ?symbol= parameter' }, 400);

  const fmpUrl = `${FMP_BASE}/key-metrics-ttm/${symbol}?apikey=${env.FMP_API_KEY}`;
  return await cachedFetch(fmpUrl, `metrics:${symbol}`, env, ctx);
}

// --- Helpers ---

async function cachedFetch(fmpUrl, cacheKey, env, ctx) {
  // Try Cloudflare Cache API first
  const cache = caches.default;
  const cacheRequest = new Request(`https://cache.internal/${cacheKey}`);
  
  let response = await cache.match(cacheRequest);
  if (response) {
    // Clone and add CORS headers
    const body = await response.text();
    return new Response(body, {
      headers: {
        ...CORS_HEADERS,
        'Content-Type': 'application/json',
        'X-Cache': 'HIT',
        'Cache-Control': `public, max-age=${CACHE_TTL}`,
      }
    });
  }

  // Cache miss — fetch from FMP
  const fmpResponse = await fetch(fmpUrl);
  if (!fmpResponse.ok) {
    const errText = await fmpResponse.text();
    return jsonResponse({ error: 'FMP API error', status: fmpResponse.status, detail: errText }, fmpResponse.status);
  }

  const data = await fmpResponse.text();
  
  // Build response with CORS + cache headers
  response = new Response(data, {
    headers: {
      ...CORS_HEADERS,
      'Content-Type': 'application/json',
      'X-Cache': 'MISS',
      'Cache-Control': `public, max-age=${CACHE_TTL}`,
    }
  });

  // Store in cache (non-blocking)
  ctx.waitUntil(cache.put(cacheRequest, new Response(data, {
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': `public, max-age=${CACHE_TTL}`,
    }
  })));

  return response;
}

function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data, null, 2), {
    status,
    headers: {
      ...CORS_HEADERS,
      'Content-Type': 'application/json',
    }
  });
}
