from flask import Flask, render_template, redirect, url_for

app = Flask(__name__)

@app.route("/RiskReport")
def report():
    return render_template("RiskReport.html",

        # ── Cover / Header ──────────────────────────────────────
        client_name         = "Susan Burke",
        address             = "2216 Atlantic Ave, Sullivan's Island, SC 29482",
        date                = "April 10, 2026",
        year                = "2026",
        latitude            = "32.7652",
        longitude           = "79.8472",

        # ── Executive Summary ───────────────────────────────────
        overall_risk        = "Very High",
        exec_summary        = (
            "This property on Sullivan's Island, South Carolina sits on a low-elevation barrier island "
            "in FEMA's highest coastal flood classification — Zone VE, with a Base Flood Elevation of 16 ft NAVD88. "
            "The site faces compounding risks: an accelerating local sea level rise rate of 3.73 mm/year at the "
            "Charleston tide gauge, a NOAA-projected intermediate rise of 1.6 ft by 2050, and Category 3 storm surge "
            "depths estimated at 10–12 ft above ground level. Sullivan's Island has a well-documented history of "
            "major hurricane strikes, and NFIP claims data for zip code 29482 reflect repeated, high-value flood "
            "losses. High tide flooding is already occurring and is projected to intensify significantly by mid-century. "
            "Any long-term investment decision for this parcel should account for substantially increasing insurance "
            "costs, potential financing constraints, and structural adaptation requirements."
        ),

        # ── Location & Context ──────────────────────────────────
        distance_to_shore   = "Approximately 0.2 miles to Atlantic Ocean shoreline",
        coastal_region      = "South Carolina Lowcountry — Charleston Metro Coast",
        location_context    = (
            "Sullivan's Island is a narrow barrier island approximately 4 miles long and 0.5 miles wide, "
            "situated at the mouth of Charleston Harbor. The island is bounded by the Atlantic Ocean to the "
            "northeast and the Intracoastal Waterway to the southwest, leaving properties exposed to surge "
            "from multiple directions during major hurricane events. Mean land elevation on the island ranges "
            "from approximately 5 to 10 feet NAVD88, with some areas well below the Base Flood Elevation. "
            "The island's barrier island geomorphology — characterized by mobile, sandy substrate and "
            "dynamic shoreline processes — makes it inherently more vulnerable than mainland or high-bluff "
            "coastal settings. The nearest NOAA tide gauge is located at Charleston, SC (Station 8665530), "
            "approximately 6 miles southwest."
        ),

        # ── Geomorphology (also used in CVI section) ────────────
        geomorphology_type  = "Barrier Island — Sandy Beach / Back-Barrier Marsh",
        geomorphology_rating= "Very High",
        geomorphology_note  = (
            "Barrier islands are among the most dynamically unstable coastal landforms. "
            "Sandy substrates and low elevations make them highly susceptible to both "
            "storm overwash and long-term sea level encroachment."
        ),

        # ── FEMA Flood Zone ─────────────────────────────────────
        flood_zone          = "VE",
        sfha                = True,
        sfha_label          = "Special Flood Hazard Area",
        base_flood_elevation= "16 ft NAVD88",
        mandatory_insurance = True,
        nfip_community_name = "Town of Sullivan's Island, SC (CID: 450176)",
        nfip_crs_rating     = "Class 5 — 25% NFIP premium discount",
        annual_flood_chance = "1% annual chance (100-year flood); 26% chance over 30-year mortgage",
        fema_note           = (
            "Zone VE is FEMA's highest coastal flood risk designation, indicating a 1% annual chance of "
            "flooding with associated wave action of 3 feet or more. Properties in Zone VE require "
            "federally-backed mortgage holders to maintain flood insurance, and new construction must "
            "be elevated above the Base Flood Elevation. Sullivan's Island participates in the Community "
            "Rating System (CRS) at Class 5, meaning policyholders receive a 25% discount on NFIP premiums "
            "— a meaningful offset given the high base rates in this zone. However, NFIP Risk Rating 2.0 "
            "(introduced in 2021) has moved premiums toward true actuarial risk, and future rate trajectories "
            "for VE properties are expected to increase substantially."
        ),

        # ── Sea Level Rise ──────────────────────────────────────
        slr_tide_gauge      = "Charleston, SC (NOAA Station 8665530)",
        slr_rate_local      = "3.73",
        slr_gauge_period    = "Based on 1921–2023 tide gauge record (NOAA CO-OPS)",

        # NOAA 2022 Interagency Scenarios — relative to 2000 baseline, Charleston gauge
        slr_low_2030        = "0.2",
        slr_low_2050        = "0.4",
        slr_low_2075        = "0.7",
        slr_low_2100        = "1.0",

        slr_intermediate_2030 = "0.3",
        slr_intermediate_2050 = "1.6",
        slr_intermediate_2075 = "2.0",
        slr_intermediate_2100 = "3.5",

        slr_high_2030       = "0.4",
        slr_high_2050       = "1.1",
        slr_high_2075       = "2.6",
        slr_high_2100       = "5.5",

        sea_level_intro     = (
            "The Charleston, SC tide gauge has recorded a local relative sea level rise rate of 3.73 mm/year — "
            "one of the higher rates on the US East Coast, reflecting both global ocean warming and local "
            "land subsidence. This rate has accelerated in recent decades. NOAA's 2022 Interagency Sea Level "
            "Rise Scenarios project that under an intermediate planning scenario, the Charleston area will see "
            "approximately 1.6 feet of additional sea level by 2050 relative to 2000 baseline levels. Under a "
            "high scenario — reflecting accelerated Antarctic and Greenland ice sheet loss — that figure rises "
            "to 5.5 feet by 2100. The satellite imagery below illustrates projected inundation extent at this "
            "parcel under the intermediate scenario."
        ),
        property_note       = (
            "At this parcel's elevation, even the low NOAA scenario projects meaningful increases in flood "
            "frequency within the investment horizon of most coastal real estate. The intermediate scenario "
            "suggests that by 2075, areas currently flooded only during major storm events may experience "
            "regular tidal inundation. Development decisions should incorporate freeboard above current BFE "
            "to account for this trajectory."
        ),

        # ── Storm Surge ─────────────────────────────────────────
        cat1_surge          = 2,
        cat2_surge          = 6,
        cat3_surge          = 10,
        cat4_surge          = 14,
        cat5_surge          = 17,

        storm_surge_intro   = (
            "Sullivan's Island is directly exposed to Atlantic hurricane storm surge with no significant "
            "offshore barrier protection. Surge depths are estimated using NOAA's SLOSH Maximum of Maximums "
            "(MOM) product, which represents the upper envelope of modeled surge heights across thousands of "
            "synthetic storm tracks making landfall near this location. These figures represent worst-case "
            "estimates for each category and should be interpreted as planning-level bounds rather than "
            "precise predictions. The interactive simulation below provides a visual reference for how "
            "increasing surge depths interact with a typical coastal structure."
        ),
        storm_surge_property_note = (
            "Based on SLOSH MOM data, a landfalling Category 3 hurricane could produce surge of 10 to 12 feet "
            "at this location — well above the first-floor finished floor elevation of most existing structures "
            "on the island. Even a Category 1 event produces surge (2 ft) that would inundate lower-lying "
            "portions of the island. Sullivan's Island has a well-documented history of direct and near-direct "
            "hurricane strikes. Hugo (1989) produced a 20-ft surge on the northern end of the island."
        ),

        # ── CVI Factors ─────────────────────────────────────────
        erosion_rate        = "–0.5 m/year (shoreline retreat)",
        erosion_rating      = "High",
        erosion_note        = (
            "The Atlantic-facing shoreline of Sullivan's Island has experienced net erosion in recent decades, "
            "with localized hot spots retreating at rates exceeding –1.0 m/year. Beach nourishment projects "
            "have periodically offset natural losses but do not eliminate long-term vulnerability."
        ),

        sea_level_rate      = "+3.73 mm/year (relative)",
        sea_level_rating    = "High",
        sea_level_note      = (
            "The local relative SLR rate at Charleston is elevated by approximately 1 mm/year above the "
            "global mean due to regional land subsidence. This accelerates the effective rate of sea level "
            "encroachment compared to more stable coastal regions."
        ),

        tidal_range         = "5.2 ft mean tidal range (mesotidal)",
        tidal_rating        = "Moderate",
        tidal_note          = (
            "Charleston Harbor's tidal range of approximately 5 feet creates regular high-water events that "
            "amplify storm surge and contribute to increasing high tide flooding frequency as sea levels rise."
        ),

        wave_height         = "Significant wave height ~1.0–1.5 m nearshore",
        wave_rating         = "High",
        wave_note           = (
            "Atlantic-facing exposure means this stretch of coast receives persistent swell energy year-round, "
            "with significantly higher wave heights during nor'easters and tropical systems. Wave runup "
            "compounds storm surge at the shoreline."
        ),

        slope_pct           = "< 0.1% coastal slope (very flat)",
        slope_rating        = "Very High",
        slope_note          = (
            "Extremely flat inland topography means that any water reaching the island interior — whether "
            "from overwash, surge, or rainfall — spreads widely and drains slowly. This dramatically "
            "increases flood extent and duration relative to steeper coastal settings."
        ),

        # ── Historical Flood Record ──────────────────────────────
        nfip_zip            = "29482",
        nfip_claims_count   = "847",
        nfip_claims_total   = "$38.4M",
        htf_days_current    = "6",
        htf_days_2050       = "35–85",

        flood_events        = [
            {
                "year": 1989,
                "name": "Hurricane Hugo",
                "type": "Major Hurricane",
                "description": "Category 4 at landfall near McClellanville, SC. 20-ft storm surge on northern Sullivan's Island. Catastrophic structural damage across the island.",
                "damage": "$8.5B (national)"
            },
            {
                "year": 1999,
                "name": "Hurricane Floyd",
                "type": "Hurricane",
                "description": "Category 2. Significant surge and coastal flooding along Sullivan's Island and Isle of Palms. Multiple structures damaged.",
                "damage": "$1.2B (SC)"
            },
            {
                "year": 2015,
                "name": "Historic October Rainfall",
                "type": "Extreme Rainfall",
                "description": "1,000-year rainfall event across coastal SC. Extensive inland and coastal flooding. Sullivan's Island roads impassable for several days.",
                "damage": "$1.5B (SC)"
            },
            {
                "year": 2019,
                "name": "Hurricane Dorian",
                "type": "Hurricane",
                "description": "Category 2 brush. Storm surge of 3–5 ft across the Charleston metro. Flooding of low-lying roads and properties on Sullivan's Island.",
                "damage": "$187M (SC coastal)"
            },
            {
                "year": 2022,
                "name": "Hurricane Ian (Remnants)",
                "type": "Tropical Remnants",
                "description": "Tropical moisture produced sustained coastal flooding and above-normal tidal surge along the SC coast.",
                "damage": "N/A (SC impact)"
            },
        ],

        flood_history_note  = (
            "NFIP claims data for zip code 29482 reflect 847 paid claims totaling $38.4 million since the "
            "program's inception — among the highest loss concentrations in coastal South Carolina. High tide "
            "flooding at the Charleston tide gauge currently occurs approximately 6 days per year; under NOAA's "
            "intermediate sea level rise scenario, this figure is projected to rise to 35–85 days annually by "
            "2050. This metric is a leading indicator of chronic, repetitive loss risk that insurers and "
            "lenders are increasingly pricing into coastal exposure."
        ),

        # ── Insurance & Regulatory ───────────────────────────────
        insurance_requirement       = "Mandatory",
        insurance_requirement_detail= "Required for all federally-backed mortgages on properties in Zone VE. Applies at closing and must be maintained continuously.",
        estimated_nfip_premium      = "$6,000–$14,000/year",
        nfip_premium_note           = (
            "Estimated range for a residential structure in Zone VE under NFIP Risk Rating 2.0. "
            "Actual premium depends on structure type, elevation above BFE, and coverage amount. "
            "Risk Rating 2.0 moves premiums toward full actuarial cost; rates are increasing annually "
            "and are not capped for new policies."
        ),
        private_market_status       = "Limited / Withdrawing",
        private_market_note         = (
            "Multiple major carriers have reduced or eliminated coastal SC exposure. Private flood "
            "markets remain available for well-elevated structures but are pricing aggressively "
            "in Zone VE. Obtain quotes from admitted and surplus lines markets."
        ),
        state_disclosure            = "Required",
        state_disclosure_detail     = (
            "South Carolina requires sellers to disclose known flood history and FEMA flood zone "
            "designation on the residential property disclosure form (SC Code § 27-50-40). "
            "Commercial transactions are subject to negotiated disclosure obligations."
        ),
        regulatory_note             = (
            "Sullivan's Island enforces a local freeboard requirement of 2 feet above the BFE for all new "
            "construction and substantial improvements, which is more stringent than the FEMA minimum. "
            "All new development requires a Coastal Zone Management permit from the SC OCRM. The Beachfront "
            "Management Act (SC Code § 48-39-10 et seq.) restricts construction within the Setback Zone "
            "and may affect development potential on oceanfront parcels. Buyers and developers should obtain "
            "a detailed zoning and permitting review before committing capital."
        ),

        # ── Mitigation Recommendations ───────────────────────────
        recommendations     = [
            {
                "title": "Obtain a FEMA Elevation Certificate",
                "description": (
                    "An Elevation Certificate (EC) documents the structure's elevation relative to the BFE "
                    "and is required for accurate NFIP rating. If the structure is elevated above BFE, the EC "
                    "may significantly reduce flood insurance premiums. Engage a licensed land surveyor to "
                    "prepare this document prior to purchase or construction."
                )
            },
            {
                "title": "Design to at Least 2 Feet of Freeboard Above BFE",
                "description": (
                    "Given the island's CRS Class 5 requirements and the projected trajectory of sea level rise, "
                    "new construction or substantial improvements should target finished floor elevations of "
                    "at least 2 feet above the current BFE (18 ft NAVD88 minimum). Each foot of freeboard "
                    "above BFE reduces NFIP premiums and provides a buffer against future BFE revisions "
                    "and sea level rise."
                )
            },
            {
                "title": "Install Flood Vents in Enclosed Foundations",
                "description": (
                    "FEMA-compliant flood openings (vents) in any enclosed space below BFE are required in "
                    "Zone VE and help equalize hydrostatic pressure during flood events, significantly reducing "
                    "structural damage. ICC-certified engineered vents may reduce the required number of "
                    "openings compared to standard vents."
                )
            },
            {
                "title": "Evaluate Breakaway Wall Design for Below-BFE Enclosures",
                "description": (
                    "Any walls below BFE must be designed as breakaway walls per FEMA Zone VE requirements. "
                    "Breakaway walls are designed to collapse under wave and flood loads, protecting the main "
                    "structure from additional hydraulic forces. Ensure any existing enclosures comply."
                )
            },
            {
                "title": "Obtain a Private Flood Insurance Quote Alongside NFIP",
                "description": (
                    "Private flood insurance markets have expanded significantly and may offer higher coverage "
                    "limits, replacement cost for contents, and coverage for additional living expenses not "
                    "available through NFIP. Obtain competing quotes annually, particularly as NFIP Risk "
                    "Rating 2.0 premiums continue to rise."
                )
            },
            {
                "title": "Review SC OCRM Permitting Requirements Before Any Construction",
                "description": (
                    "The South Carolina Office of Coastal Resource Management (OCRM) regulates development "
                    "within critical areas and setback zones. Any new construction, renovation exceeding 25% "
                    "of structure value, or addition requires a CAMA permit and must comply with the Beachfront "
                    "Management Act setback lines. Engage a coastal permitting attorney or consultant early "
                    "in the development process."
                )
            },
        ],
    )


@app.route('/unity')
def unity_sim():
    return redirect(url_for('static', filename='HouseWebBuild/index.html'))


if __name__ == "__main__":
    app.run(debug=True)
