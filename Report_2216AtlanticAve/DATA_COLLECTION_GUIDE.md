# CoastalRisk — Report Data Collection Guide
_Use this checklist for every new client report. Each section lists what to find and exactly where to find it._

---

## Before You Start

You need the client's **full property address** and their **email address** for delivery.
Open `ReportHandler.py`, duplicate the existing `render_template()` call, and replace values as you go through this guide.

---

## 01 — Cover Info
Quick — just fill these in from the client order.

| Variable | What to put |
|----------|------------|
| `client_name` | Client's full name |
| `address` | Full property address including zip |
| `date` | Today's date |
| `year` | Current year |
| `latitude` | Look up via Google Maps (right-click → "What's here?") |
| `longitude` | Same — drop the minus sign in the template |

---

## 02 — FEMA Flood Zone
**Source: FEMA Flood Map Service Center**
🔗 https://msc.fema.gov/portal/search

1. Enter the property address
2. Open the effective FIRM panel
3. Record: **Flood Zone** (X / B / A / AE / V / VE), **Base Flood Elevation** (ft NAVD88), **FIRM panel number**

**For SFHA status:** Any zone starting with A or V = SFHA = True

**For CRS rating:**
🔗 https://www.fema.gov/flood-insurance/work-with-nfip/community-rating-system/communities
Search the community name. CRS classes run 1–10; Class 5 = 25% discount, Class 1 = 45% discount.

**For annual flood chance:**
- Zone AE/VE = "1% annual chance (100-year); 26% chance over 30-year mortgage"
- Zone X = "Less than 0.2% annual chance (500-year)"

| Variable | Source |
|----------|--------|
| `flood_zone` | FIRM map |
| `sfha` | True if A or V zone |
| `base_flood_elevation` | FIRM map — "X ft NAVD88" |
| `mandatory_insurance` | True if SFHA + federally-backed mortgage |
| `nfip_community_name` | CRS community lookup |
| `nfip_crs_rating` | CRS lookup — "Class X — Y% NFIP premium discount" |
| `annual_flood_chance` | Use standard language above |

---

## 03 — Sea Level Rise Data
**Source: NOAA CO-OPS API / Sea Level Trends**
🔗 https://tidesandcurrents.noaa.gov/sltrends/sltrends.html

1. Find the nearest tide gauge station (there's a map on that page — pick the closest one)
2. Note the **Station Name** and **Station ID**
3. Record the **relative sea level trend** in mm/year and the period of record

**For SLR projections (Low / Intermediate / High scenarios):**
🔗 https://oceanservice.noaa.gov/hazards/sealevelrise/sealevelrise-tech-report.html
OR use the Interagency Sea Level Rise tool:
🔗 https://sealevel.nasa.gov/data_tools/18
- Select your nearest tide gauge
- Scenarios: Low, Intermediate, High (use NOAA 2022 Interagency report values)
- Record feet above 2000 baseline for 2030, 2050, 2075, 2100

| Variable | Source |
|----------|--------|
| `slr_tide_gauge` | "Station Name (NOAA Station XXXXXXX)" |
| `slr_rate_local` | CO-OPS trend page — rate in mm/year |
| `slr_gauge_period` | "Based on YYYY–YYYY tide gauge record (NOAA CO-OPS)" |
| `slr_low_2030` through `slr_high_2100` | NOAA Interagency 2022 scenarios, nearest gauge |

---

## 04 — Storm Surge
**Source: NOAA NHC National Storm Surge Risk Maps**
🔗 https://www.nhc.noaa.gov/nationalsurge/

1. Click "View the maps" for the relevant coast (Gulf, Atlantic, Pacific)
2. Navigate to the property location
3. Check surge depth for Cat 1, 2, 3, 4, 5 at that location
4. These are SLOSH MOM values (Maximum of Maximums — worst case per category)

**Alternatively:** NOAA's Coastal Flood Exposure Mapper shows storm surge layers
🔗 https://coast.noaa.gov/floodexposure/

| Variable | What to record |
|----------|---------------|
| `cat1_surge` through `cat5_surge` | Integer feet from SLOSH MOM maps |

---

## 05 — Coastal Vulnerability (CVI) Factors
**Source: Your existing GeoJSON (CoastalCalculator.geojson) — already in the main app**

Run the free tool on coastalrisk.org with the property address. The results page gives you all six CVI factors. Use those values to populate:

| Variable | From free tool |
|----------|---------------|
| `erosion_rating` | Erosion levels result |
| `sea_level_rating` | Sea-level rise result |
| `tidal_rating` | Tidal risk result |
| `wave_rating` | Wave climate result |
| `slope_rating` | Coastal slope result |
| `geomorphology_rating` | Geomorphology result |

For the **metric fields** (actual measurements), look these up from USGS publications or the CVI source data:
- `erosion_rate`: shoreline change rate in m/year (USGS NASC data)
- `tidal_range`: mean tidal range in feet (NOAA CO-OPS for nearest gauge)
- `wave_height`: significant wave height in meters (NOAA buoy data or USGS)
- `slope_pct`: coastal slope as a percentage (USGS CVI source)

**For notes:** Write 2–3 sentences per factor explaining what the rating means for this specific location.

---

## 06 — Historical Flood Record

### NFIP Claims (OpenFEMA)
🔗 https://www.fema.gov/openfema-data-page/fima-nfip-redacted-claims-v2

Filter by `reportedZipCode` = property's zip code.
- Count the number of records = `nfip_claims_count`
- Sum `amountPaidOnBuildingClaim` + `amountPaidOnContentsClaim` = `nfip_claims_total`

You can do this in Excel or use the OpenFEMA API directly.

### Storm Events (NOAA NCEI)
🔗 https://www.ncei.noaa.gov/stormevents/

1. Select state and county
2. Filter for flood-related event types: Coastal Flood, Flash Flood, Hurricane, Tropical Storm, Storm Surge/Tide
3. Pull 5–10 most significant events with year, name, damage, description

### High Tide Flooding
🔗 https://tidesandcurrents.noaa.gov/high-tide-flooding/annual-outlook.html

Find the nearest gauge. Look up:
- Current HTF days/year = `htf_days_current`
- NOAA intermediate 2050 projection = `htf_days_2050`

| Variable | Source |
|----------|--------|
| `nfip_zip` | Property zip code |
| `nfip_claims_count` | OpenFEMA filtered count |
| `nfip_claims_total` | OpenFEMA summed payouts (format as "$X.XM") |
| `htf_days_current` | NOAA HTF annual outlook |
| `htf_days_2050` | NOAA HTF outlook (format as "XX–XX") |
| `flood_events` | List of dicts — see ReportHandler.py for format |

---

## 07 — Insurance & Regulatory

### Insurance
- NFIP premium estimate: Use FEMA's flood insurance rate estimator at
  🔗 https://www.fema.gov/flood-insurance/find-flood-insurance
  Or provide a range based on zone + structure type research
- Private market: Research carrier availability in the state (check AM Best, Demotech)

### State Disclosure & Regulatory
Research the state's specific requirements:
- Does the state require flood zone disclosure on the property disclosure form?
- Are there local freeboard requirements above BFE?
- Is there a Coastal Zone Management / CAMA-type permit required?
- Any state-specific beachfront management acts or setback rules?

**South Carolina reference:** SC OCRM — https://www.scdhec.gov/environment/ocrm
**Florida reference:** FDEP Beaches — https://floridadep.gov/water/beaches
**North Carolina reference:** NC DCM — https://www.deq.nc.gov/about/divisions/coastal-management

| Variable | Source |
|----------|--------|
| `insurance_requirement` | "Mandatory" or "Not Required" |
| `estimated_nfip_premium` | Range from FEMA estimator |
| `private_market_status` | "Available" / "Limited" / "Withdrawing" |
| `state_disclosure` | "Required" / "Not Required" |

---

## 08 — Mitigation Recommendations
These are largely property-type and zone-specific. Adapt from the Sullivan's Island template in `ReportHandler.py`. Key recommendations that almost always apply to coastal properties:

- Elevation Certificate (always recommend if not already obtained)
- Freeboard above BFE (especially for VE/AE zones)
- Flood vents / breakaway walls (VE zones)
- Private flood insurance quotes (all SFHA properties)
- State coastal permitting review (any development)

Add property-specific ones based on what you found in your research (e.g., proximity to inlet = higher erosion risk; low BFE = recommend higher elevation; etc.)

---

## 09 — QGIS Maps to Create
These are the images you produce manually in QGIS and save to `Report_2216AtlanticAve/static/` (or a new folder for the new client).

| File | What it shows |
|------|--------------|
| `SLR_2030.png` | NOAA SLR viewer screenshot — intermediate scenario, 2030 extent, property highlighted |
| `SLR_2055.png` | Same — 2055 extent |
| `SLR_2075.png` | Same — 2075 extent |
| `surge1.png` through `surge5.png` | NOAA Coastal Flood Exposure Mapper — storm surge Cat 1–5 layers, property highlighted |

**Workflow:**
1. Open NOAA Sea Level Rise Viewer (coast.noaa.gov/slr) — navigate to property
2. Set scenario and year — screenshot or export
3. Open NOAA Coastal Flood Exposure Mapper — add storm surge layers
4. Export images at consistent zoom level with property clearly marked
5. Crop to a consistent aspect ratio (recommend ~4:3)

---

## Checklist Before Sending
- [ ] All template variables filled in (no `{{ placeholder }}` left in the rendered report)
- [ ] QGIS images created and saved to the correct static folder
- [ ] Report route tested locally at `localhost:5000/RiskReport`
- [ ] Surge depths verified against NOAA NHC maps
- [ ] FEMA zone and BFE confirmed against FIRM panel
- [ ] SLR projections sourced from the correct tide gauge station
- [ ] NFIP claims data pulled for correct zip code
- [ ] Flood events list includes at least 3–5 real events with citations
- [ ] Mitigation recommendations are property-specific, not generic
- [ ] Disclaimer and data sources footer are accurate
- [ ] Proofread for client name, address, date consistency throughout
