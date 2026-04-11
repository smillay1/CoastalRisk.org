# CoastalRisk — Codebase Map
_Last updated: April 2026_

---

## Architecture Overview

CoastalRisk is a Python/Flask web application deployed on Heroku. There are two
separate Flask apps in the repo that run independently:

```
coastalrisk.org
      │
      ▼
┌─────────────────────────────────────────────────────┐
│              SeasFuture.py  (main app)              │
│              Heroku · gunicorn · port 5001 (local)  │
│                                                     │
│  Routes:                                            │
│    GET  /           → index.html (homepage)         │
│    POST /results    → results.html (CVI lookup)     │
│    GET  /premium    → premium.html (order page)     │
│    GET  /payment    → payment.html (legacy)         │
│    GET  /success    → success.html (post-payment)   │
│    POST /create-checkout-session  → Stripe          │
│    POST /create-payment-intent    → Stripe          │
│    GET  /get-stripe-public-key    → Stripe pubkey   │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│        ReportHandler.py  (sample report app)        │
│        Runs separately · port 5000 (local)          │
│                                                     │
│  Routes:                                            │
│    GET  /RiskReport → RiskReport.html (full report) │
│    GET  /unity      → Unity WebGL simulation        │
└─────────────────────────────────────────────────────┘
```

---

## User Flows

### 1 — Free Risk Calculator
```
User lands on homepage (/)
  └─► Enters a US coastal address
        └─► Form POST → /results
              ├─► Google Maps Geocoding API (address → lat/lng)
              ├─► Haversine search through CoastalCalculator.geojson
              │     (finds nearest USGS data point within 20 miles)
              └─► Renders results.html with:
                    CVI, erosion, sea_level, tides,
                    geomorphology, waves, slope
                    + Google Maps embed showing address
                      and nearest data point
```

### 2 — Paid Report (Consumer)
```
User visits /premium
  └─► Clicks "Order Your Report"
        └─► JS POST → /create-checkout-session
              └─► Stripe creates hosted checkout session
                    └─► User redirected to Stripe payment page
                          ├─► On success → /success (confirmation page)
                          └─► On cancel  → /premium
```

### 3 — Sample/Client Report (Dev only)
```
Run Report_2216AtlanticAve/ReportHandler.py separately
  └─► Visit localhost:5000/RiskReport
        └─► Renders full report for "2216 Atlantic Ave, Sullivan's Island, SC"
              Sections: Risk Snapshot, Sea Level Rise (2030/2055/2075),
              Storm Surge (Cat 1–5 carousel), Unity sim, FEMA zone,
              Historic flood timeline
```

---

## File-by-File Reference

### Root
| File | Purpose |
|------|---------|
| `SeasFuture.py` | Main Flask app — all routes, API calls, data logic |
| `CoastalCalculator.geojson` | **Core data asset.** USGS Coastal Vulnerability Index data for the entire US coastline. Every free tool query runs against this. |
| `SeasFuture.env` | Environment variables: `GOOGLE_MAPS_API_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_PUBLIC_KEY` |
| `SeasFuture.qmd` | QGIS project metadata — used when working with the GeoJSON in QGIS desktop app |
| `requirements.txt` | Python dependencies (Flask, stripe, haversine, requests, gunicorn) |
| `Procfile` | Heroku run command: `web: gunicorn SeasFuture:app` |
| `CNAME` | Points `coastalrisk.org` to Heroku |
| `package.json` + `js/server.js` | **Legacy Node.js server** — not part of the live deployment (Heroku runs Python). Appears to be an earlier prototype. Can be ignored for now. |
| `cors.json` | CORS config reference file (not actively loaded by Flask — CORS is set in code) |

### templates/
| File | Status | Purpose |
|------|--------|---------|
| `index.html` | ✅ Active | Homepage — hero, free calculator form, mission + philosophy sections |
| `results.html` | ✅ Active | CVI results page — 6 risk factor cards with sliders, Google Map |
| `premium.html` | ✅ Active | Order page — redesigned April 2026 to match dark theme |
| `success.html` | ✅ Active | Post-payment confirmation — added April 2026 |
| `payment.html` | ⚠️ Legacy | Older standalone checkout page — duplicates premium.html functionality, nothing links to it. Safe to delete eventually. |
| `donate.html` | ⚠️ Orphaned | Donation page with Venmo/PayPal links. No route in SeasFuture.py, completely unreachable. Safe to delete or wire up. |

### static/
| File | Purpose |
|------|---------|
| `background.jpeg` | Full-page hero background image (ocean) |
| `favicon.png` | Brand icon (wave) — used in all navbars |
| `philosophy.jpeg` | Appears in static folder, not currently referenced in active templates |
| `floodrisk.png`, `satellite.png`, `development.png` | Marketing/section images — available but not all in active use |
| `newwave.png`, `newwaves.png` | Wave graphics — used in donate.html |

### Report_2216AtlanticAve/
| File | Purpose |
|------|---------|
| `ReportHandler.py` | Standalone Flask app for serving the sample client report |
| `templates/RiskReport.html` | Full report template — parameterized via Jinja2 |
| `static/SLR_2030.png` etc. | Sea level rise projection maps for Sullivan's Island |
| `static/surge1–5.png` | Storm surge imagery per hurricane category |
| `static/ramp.png` | Visual used in report |
| `static/HouseWebBuild/` | Unity WebGL build — interactive storm surge house simulation |

---

## Key External Dependencies

| Service | Used For | Where |
|---------|---------|-------|
| Google Maps Geocoding API | Address → lat/lng | `/results` in SeasFuture.py |
| Google Maps JS API | Map embed on results page | results.html |
| Stripe | Payment processing | `/create-checkout-session`, premium.html |
| USGS Coastal Change Hazards Portal | Source of CoastalCalculator.geojson | Data asset |
| Heroku | App hosting + deployment | Procfile |

---

## Known Issues / Things to Address

| Issue | Priority | Notes |
|-------|----------|-------|
| No automated report delivery | 🔴 High | Payment goes through but no report is generated or emailed automatically. Currently manual. |
| No Stripe webhook / payment notification | 🔴 High | No way to know a payment happened without checking Stripe dashboard |
| `payment.html` is dead code | 🟡 Medium | Nothing routes to it — safe to delete |
| `donate.html` has no Flask route | 🟡 Medium | Unreachable — either wire it up or delete |
| Historic flood events in RiskReport are hardcoded | 🟡 Medium | Two placeholder events, not property-specific data |
| `server.js` / Node dependencies are unused | 🟢 Low | Leftover prototype — can clean up |
| No B2B developer landing page | 🔴 High | In progress |
| CORS only allows coastalrisk.org | 🟢 Low | Fine for production, just remember for local dev testing |

---

## Local Development

### Main app
```bash
cd ~/Desktop/Seas
pip install -r requirements.txt   # first time only
python SeasFuture.py
# → http://localhost:5001
```

### Sample report
```bash
cd ~/Desktop/Seas/Report_2216AtlanticAve
python ReportHandler.py
# → http://localhost:5000/RiskReport
```

### Pages to test locally
| URL | What you're testing |
|-----|-------------------|
| `localhost:5001/` | Homepage + free calculator |
| `localhost:5001/results` | (POST only — submit from homepage) |
| `localhost:5001/premium` | Redesigned order page |
| `localhost:5001/success` | Post-payment confirmation |
| `localhost:5000/RiskReport` | Full client report (separate app) |

---

## What "premium" means right now vs. future state

**Current:** User pays $39 via Stripe → lands on /success → report is assembled and sent manually by Sam.

**Target:** User pays → Stripe webhook fires → report auto-generated from address data → emailed via SendGrid/similar → no manual step required.

The report template (RiskReport.html) and the data pipeline (SeasFuture.py + GeoJSON) are already built. The missing piece is the glue between payment and delivery.
