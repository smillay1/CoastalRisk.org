from flask import Flask, render_template, request, jsonify, url_for
from flask_cors import CORS
import os
import requests
import json
from haversine import haversine, Unit
import urllib.parse
import stripe
import jinja2

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["https://coastalrisk.org"]}})

# Allow Flask to find templates in both the main templates/ folder
# and the Report_2216AtlanticAve/templates/ subfolder
app.jinja_loader = jinja2.ChoiceLoader([
    app.jinja_loader,
    jinja2.FileSystemLoader('Report_2216AtlanticAve/templates'),
])

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Load GeoJSON
def load_geojson():
    try:
        with open('CoastalCalculator.geojson', 'r') as file:
            geojson_data = json.load(file)
            print("GeoJSON data loaded successfully")
            return geojson_data
    except Exception as e:
        print(f"Error loading GeoJSON data: {e}")
        return None

geojson_data = load_geojson()




# Load env with its variables
def load_env():
    try:
        with open('./SeasFuture.env', 'r') as file:
            for line in file:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
            print("Environment variables loaded successfully")
    except Exception as e:
        print(f"Error loading environment variables: {e}")

load_env()


@app.route('/')
def index():
    try:
        css_url = url_for('static', filename='css/styles.css')
        print(f"Index route accessed, CSS URL: {css_url}")
        return render_template('index.html', css_url=css_url)
    except Exception as e:
        print(f"Error in index route: {e}")
        return "Error loading index page", 500

@app.route('/results', methods=['POST'])
def results():
    try:
        # Fetching the user's input
        address = request.form['address']
        print(f"Address received: {address}")

        # Google Maps Geocoding API setup
        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        address_encoded = urllib.parse.quote_plus(address)
        geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address_encoded}&key={api_key}"

        response = requests.get(geocode_url)
        if response.status_code == 200:
            data = response.json()
            if data['results']:
                latitude = data['results'][0]['geometry']['location']['lat']
                longitude = data['results'][0]['geometry']['location']['lng']
                print(f"Coordinates: {latitude}, {longitude}")

                # Call the function to find the coastal vulnerability data
                closest_feature = find_closest_feature(longitude, latitude)
                feature_lat, feature_lng = get_feature_lat_lng(longitude, latitude)
                if closest_feature:
                    coastal_vulnerability_data = get_coastal_data_from_feature(closest_feature)
                    return render_template('results.html', address=address, results=coastal_vulnerability_data, latitude=latitude, longitude=longitude, GOOGLE_MAPS_API_KEY=api_key, feature_lat=feature_lat, feature_lng = feature_lng)
                else:
                    return jsonify({"error": "Your location is too far from the coast."}), 404
            else:
                return jsonify({"error": "No geocoding results found."}), 404

        else:
            error_message = response.text
            print(f"Geocoding API error: {error_message}")
            return jsonify({'error': 'Geocoding API error', 'message': error_message}), response.status_code

    except Exception as e:
        print(f"Error in results route: {str(e)}")
        return "Error processing request", 500

@app.route('/create-payment-intent', methods=['POST'])
def create_payment():
    try:
        data = request.get_json()
        amount = data.get('amount')

        
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',
            automatic_payment_methods={"enabled": True}
        )

        return jsonify({"clientSecret": intent.client_secret})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get-stripe-public-key", methods=["GET"])
def get_stripe_public_key():
    return jsonify({"publicKey": os.getenv("STRIPE_PUBLIC_KEY")})

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Coastal Risk Report',
                    },
                    'unit_amount': 3900,  # $39.00 in cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url='https://coastalrisk.org/success',
            cancel_url='https://coastalrisk.org/developers',
        )
        return jsonify({'url': checkout_session.url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/developers")
def developers():
    return render_template("developers.html", year="2026")

@app.route("/RiskReport")
def risk_report():
    return render_template("RiskReport.html",
        client_name         = "Susan Burke",
        address             = "2216 Atlantic Ave, Sullivan's Island, SC 29482",
        date                = "April 10, 2026",
        year                = "2026",
        latitude            = "32.7652",
        longitude           = "79.8472",
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
        geomorphology_type  = "Barrier Island — Sandy Beach / Back-Barrier Marsh",
        geomorphology_rating= "Very High",
        geomorphology_note  = (
            "Barrier islands are among the most dynamically unstable coastal landforms. "
            "Sandy substrates and low elevations make them highly susceptible to both "
            "storm overwash and long-term sea level encroachment."
        ),
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
        slr_tide_gauge      = "Charleston, SC (NOAA Station 8665530)",
        slr_rate_local      = "3.73",
        slr_gauge_period    = "Based on 1921–2023 tide gauge record (NOAA CO-OPS)",
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
        nfip_zip            = "29482",
        nfip_claims_count   = "847",
        nfip_claims_total   = "$38.4M",
        htf_days_current    = "6",
        htf_days_2050       = "35–85",
        flood_events        = [
            {"year": 1989, "name": "Hurricane Hugo", "type": "Major Hurricane",
             "description": "Category 4 at landfall near McClellanville, SC. 20-ft storm surge on northern Sullivan's Island. Catastrophic structural damage across the island.",
             "damage": "$8.5B (national)"},
            {"year": 1999, "name": "Hurricane Floyd", "type": "Hurricane",
             "description": "Category 2. Significant surge and coastal flooding along Sullivan's Island and Isle of Palms. Multiple structures damaged.",
             "damage": "$1.2B (SC)"},
            {"year": 2015, "name": "Historic October Rainfall", "type": "Extreme Rainfall",
             "description": "1,000-year rainfall event across coastal SC. Extensive inland and coastal flooding. Sullivan's Island roads impassable for several days.",
             "damage": "$1.5B (SC)"},
            {"year": 2019, "name": "Hurricane Dorian", "type": "Hurricane",
             "description": "Category 2 brush. Storm surge of 3–5 ft across the Charleston metro. Flooding of low-lying roads and properties on Sullivan's Island.",
             "damage": "$187M (SC coastal)"},
            {"year": 2022, "name": "Hurricane Ian (Remnants)", "type": "Tropical Remnants",
             "description": "Tropical moisture produced sustained coastal flooding and above-normal tidal surge along the SC coast.",
             "damage": "N/A (SC impact)"},
        ],
        flood_history_note  = (
            "NFIP claims data for zip code 29482 reflect 847 paid claims totaling $38.4 million since the "
            "program's inception — among the highest loss concentrations in coastal South Carolina. High tide "
            "flooding at the Charleston tide gauge currently occurs approximately 6 days per year; under NOAA's "
            "intermediate sea level rise scenario, this figure is projected to rise to 35–85 days annually by "
            "2050. This metric is a leading indicator of chronic, repetitive loss risk that insurers and "
            "lenders are increasingly pricing into coastal exposure."
        ),
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
        recommendations     = [
            {"title": "Obtain a FEMA Elevation Certificate",
             "description": (
                "An Elevation Certificate (EC) documents the structure's elevation relative to the BFE "
                "and is required for accurate NFIP rating. If the structure is elevated above BFE, the EC "
                "may significantly reduce flood insurance premiums. Engage a licensed land surveyor to "
                "prepare this document prior to purchase or construction."
             )},
            {"title": "Design to at Least 2 Feet of Freeboard Above BFE",
             "description": (
                "Given the island's CRS Class 5 requirements and the projected trajectory of sea level rise, "
                "new construction or substantial improvements should target finished floor elevations of "
                "at least 2 feet above the current BFE (18 ft NAVD88 minimum). Each foot of freeboard "
                "above BFE reduces NFIP premiums and provides a buffer against future BFE revisions "
                "and sea level rise."
             )},
            {"title": "Install Flood Vents in Enclosed Foundations",
             "description": (
                "FEMA-compliant flood openings (vents) in any enclosed space below BFE are required in "
                "Zone VE and help equalize hydrostatic pressure during flood events, significantly reducing "
                "structural damage. ICC-certified engineered vents may reduce the required number of "
                "openings compared to standard vents."
             )},
            {"title": "Evaluate Breakaway Wall Design for Below-BFE Enclosures",
             "description": (
                "Any walls below BFE must be designed as breakaway walls per FEMA Zone VE requirements. "
                "Breakaway walls are designed to collapse under wave and flood loads, protecting the main "
                "structure from additional hydraulic forces. Ensure any existing enclosures comply."
             )},
            {"title": "Obtain a Private Flood Insurance Quote Alongside NFIP",
             "description": (
                "Private flood insurance markets have expanded significantly and may offer higher coverage "
                "limits, replacement cost for contents, and coverage for additional living expenses not "
                "available through NFIP. Obtain competing quotes annually, particularly as NFIP Risk "
                "Rating 2.0 premiums continue to rise."
             )},
            {"title": "Review SC OCRM Permitting Requirements Before Any Construction",
             "description": (
                "The South Carolina Office of Coastal Resource Management (OCRM) regulates development "
                "within critical areas and setback zones. Any new construction, renovation exceeding 25% "
                "of structure value, or addition requires a CAMA permit and must comply with the Beachfront "
                "Management Act setback lines. Engage a coastal permitting attorney or consultant early "
                "in the development process."
             )},
        ],
    )

@app.route("/RiskReport/FortMyersBeach")
def risk_report_fmb():
    return render_template("RiskReport.html",
        client_name         = "Sample Report — CoastalRisk",
        address             = "1000 Estero Blvd, Fort Myers Beach, FL 33931",
        date                = "April 2026",
        year                = "2026",
        latitude            = "26.4526",
        longitude           = "81.9495",
        overall_risk        = "Very High",
        exec_summary        = (
            "This property on Estero Island — the barrier island community of Fort Myers Beach, Florida — "
            "sits in FEMA Zone VE with a Base Flood Elevation of 14 ft NAVD88, directly in the path of "
            "Gulf of Mexico hurricane storm surge. Hurricane Ian made landfall just south of this location "
            "on September 28, 2022 as a Category 4 storm, producing 12–18 feet of surge that destroyed or "
            "severely damaged the overwhelming majority of structures on the island. NFIP paid claims in "
            "zip code 33931 totaled over $312 million in the Ian aftermath alone — the largest single-event "
            "concentration of claims in Florida NFIP history. The private insurance market in Southwest "
            "Florida has effectively collapsed: Heritage Insurance exited the state, multiple carriers "
            "suspended new policies, and Citizens Property Insurance is now the primary insurer for most "
            "coastal properties. NOAA projects local sea levels to rise 1.5 feet under the intermediate "
            "scenario by 2050, compounding already catastrophic surge and chronic flood risk. This parcel "
            "represents one of the highest coastal risk profiles in the continental United States."
        ),
        distance_to_shore   = "Approximately 0.1 miles to Gulf of Mexico shoreline",
        coastal_region      = "Southwest Florida Gulf Coast — Lee County",
        location_context    = (
            "Estero Island is a narrow Gulf-barrier island approximately 7 miles long and 0.5 miles wide, "
            "connected to the mainland only by a single causeway (Matanzas Pass Bridge). The island is "
            "bounded by the Gulf of Mexico to the west and Estero Bay Aquatic Preserve to the east. "
            "This configuration — barrier island with single egress point — creates extreme vulnerability "
            "to surge from Gulf-tracking hurricanes. With no significant offshore shoals or islands to "
            "attenuate storm energy, surge can arrive at full Gulf intensity. The island's mean elevation "
            "is approximately 3–5 ft NAVD88, well below the 14 ft BFE, meaning the entire island is "
            "subject to inundation in major hurricane events. The nearest NOAA tide gauge is located at "
            "Fort Myers, FL (Station 8725520), approximately 12 miles to the east via Matanzas Pass."
        ),
        geomorphology_type  = "Barrier Island — Gulf-Facing Sandy Beach / Back-Bay Estuary",
        geomorphology_rating= "Very High",
        geomorphology_note  = (
            "Gulf-facing barrier islands experience some of the most intense storm surge dynamics on the "
            "US coast. The low relief, sandy substrate, and single-causeway connectivity create extreme "
            "vulnerability. Hurricane Ian demonstrated that even well-built elevated structures cannot "
            "survive direct Cat 4 surge on this island."
        ),
        flood_zone          = "VE",
        sfha                = True,
        sfha_label          = "Special Flood Hazard Area",
        base_flood_elevation= "14 ft NAVD88",
        mandatory_insurance = True,
        nfip_community_name = "City of Fort Myers Beach, FL (CID: 120159)",
        nfip_crs_rating     = "Class 8 — 10% NFIP premium discount",
        annual_flood_chance = "1% annual chance (100-year flood); 26% chance over 30-year mortgage",
        fema_note           = (
            "Zone VE is FEMA's highest coastal flood risk designation, indicating a 1% annual chance of "
            "flooding with associated wave action of 3 feet or more. Fort Myers Beach participates in the "
            "Community Rating System at Class 8, providing a 10% premium discount — modest relief given "
            "the elevated base rates in VE zones following Risk Rating 2.0 implementation in 2021. "
            "Post-Ian FEMA preliminary damage assessments resulted in proposed map revisions that expand "
            "VE zones on Estero Island. Buyers should verify current FIRM panel status as remapping "
            "is ongoing. Properties being rebuilt post-Ian are subject to substantial improvement rules "
            "requiring compliance with current flood zone standards."
        ),
        slr_tide_gauge      = "Fort Myers, FL (NOAA Station 8725520)",
        slr_rate_local      = "2.38",
        slr_gauge_period    = "Based on 1965–2023 tide gauge record (NOAA CO-OPS)",
        slr_low_2030        = "0.2",
        slr_low_2050        = "0.4",
        slr_low_2075        = "0.6",
        slr_low_2100        = "0.9",
        slr_intermediate_2030 = "0.3",
        slr_intermediate_2050 = "1.5",
        slr_intermediate_2075 = "2.2",
        slr_intermediate_2100 = "3.7",
        slr_high_2030       = "0.4",
        slr_high_2050       = "1.2",
        slr_high_2075       = "2.9",
        slr_high_2100       = "5.8",
        sea_level_intro     = (
            "The Fort Myers tide gauge has recorded a local relative sea level rise rate of 2.38 mm/year "
            "since 1965 — below the Charleston rate but highly significant given the extremely low base "
            "elevation of Estero Island. Under NOAA's 2022 intermediate planning scenario, Southwest "
            "Florida will experience approximately 1.5 feet of additional sea level by 2050 relative to "
            "year 2000 baseline. Even the low scenario projects meaningful increases in chronic tidal "
            "flooding frequency by mid-century. At an island mean elevation of 3–5 ft NAVD88, incremental "
            "sea level rise directly increases the frequency and depth of all storm surge events and "
            "accelerates the transition from periodic to chronic flooding."
        ),
        property_note       = (
            "At this parcel's elevation, the intermediate SLR scenario would render the current ground "
            "floor unusable for storage or habitation within the investment horizon of most coastal real "
            "estate. Post-Ian rebuilding to current BFE provides some buffer, but future BFE revisions "
            "and sea level rise compound. Development decisions should target finished floor elevations "
            "significantly above current BFE minimums."
        ),
        cat1_surge          = 3,
        cat2_surge          = 7,
        cat3_surge          = 12,
        cat4_surge          = 16,
        cat5_surge          = 20,
        storm_surge_intro   = (
            "Estero Island is one of the most surge-exposed locations on the Gulf of Mexico coast. "
            "Surge depths are estimated using NOAA's SLOSH Maximum of Maximums (MOM) product for the "
            "SW Florida basin (SFL3), representing the upper envelope of modeled surge heights across "
            "thousands of synthetic storm tracks. Hurricane Ian (2022) produced measured surge of "
            "12–18 feet on the island as a Category 4 event — consistent with SLOSH MOM projections "
            "and demonstrating that these are not theoretical maximums but historically validated events. "
            "The island's single-causeway connection creates an additional life-safety risk: evacuation "
            "windows are extremely limited once surge begins."
        ),
        storm_surge_property_note = (
            "Hurricane Ian's surge effectively validated the SLOSH MOM model for this location: the "
            "observed 12–18 ft surge matched Category 4 model projections within normal uncertainty bounds. "
            "The majority of structures not elevated to or above BFE were destroyed or rendered uninhabitable. "
            "Any structure rebuilt or constructed at this location must be designed to withstand Cat 4-equivalent "
            "surge as a baseline planning assumption, given the historical frequency of major landfalls in "
            "this basin (Ian 2022, Charley 2004, Donna 1960)."
        ),
        erosion_rate        = "–0.7 m/year (Gulf-facing shoreline retreat)",
        erosion_rating      = "High",
        erosion_note        = (
            "The Gulf-facing beach of Estero Island has experienced consistent net erosion. Beach "
            "nourishment projects have been conducted periodically but cannot offset the long-term "
            "sediment deficit. Post-Ian shoreline surveys showed significant retreat across the island."
        ),
        sea_level_rate      = "+2.38 mm/year (relative, Fort Myers gauge)",
        sea_level_rating    = "Moderate",
        sea_level_note      = (
            "The local relative SLR rate is moderate compared to the Southeast Atlantic coast, but "
            "the island's extremely low base elevation means even modest sea level increases materially "
            "affect flood frequency and surge depth."
        ),
        tidal_range         = "2.1 ft mean tidal range (microtidal Gulf of Mexico)",
        tidal_rating        = "Low",
        tidal_note          = (
            "The Gulf of Mexico's microtidal environment means daily tidal fluctuations are small. "
            "This reduces chronic tidal flooding compared to mesotidal Atlantic settings, but does "
            "not reduce hurricane surge risk, which is independent of tidal range."
        ),
        wave_height         = "Significant wave height 0.5–1.0 m typical; 3–5 m during major storms",
        wave_rating         = "Moderate",
        wave_note           = (
            "Gulf fetch limitations keep typical wave heights modest. However, during direct hurricane "
            "approach, wave heights amplify rapidly and combine with surge to produce catastrophic "
            "total water levels. Hurricane Ian's wave field exceeded 10 meters offshore."
        ),
        slope_pct           = "< 0.05% coastal slope (exceptionally flat)",
        slope_rating        = "Very High",
        slope_note          = (
            "Estero Island's extremely flat topography means surge water spreads across the entire "
            "island width within minutes of arrival. There is no high ground refuge. Surge drains "
            "slowly in all directions, prolonging inundation duration significantly."
        ),
        nfip_zip            = "33931",
        nfip_claims_count   = "2,847",
        nfip_claims_total   = "$312.4M",
        htf_days_current    = "3",
        htf_days_2050       = "25–60",
        flood_events        = [
            {"year": 2022, "name": "Hurricane Ian", "type": "Major Hurricane",
             "description": "Category 4 at landfall near Cayo Costa/Fort Myers Beach (Sept 28, 2022). Storm surge of 12–18 ft on Estero Island. Largest single-event NFIP loss concentration in Florida history. Majority of island structures destroyed or rendered uninhabitable.",
             "damage": "$112B estimated (FL statewide)"},
            {"year": 2017, "name": "Hurricane Irma", "type": "Major Hurricane",
             "description": "Category 3 at FL Keys landfall, then tracked up Gulf coast as Cat 2. Storm surge 4–6 ft on SW Gulf coast. Significant flooding across Estero Island; multiple structures damaged.",
             "damage": "$50B (FL statewide)"},
            {"year": 2004, "name": "Hurricane Charley", "type": "Major Hurricane",
             "description": "Category 4 at Punta Gorda landfall (Aug 13, 2004). Storm surge 5–8 ft on Estero Island. Significant structural damage across Fort Myers Beach.",
             "damage": "$16.9B (FL statewide)"},
            {"year": 2004, "name": "Hurricane Frances", "type": "Hurricane",
             "description": "Category 2 at FL east coast (Sept 4, 2004), crossed peninsula and impacted Gulf coast with surge and rainfall. Secondary flooding event within same season as Charley.",
             "damage": "$9.5B (FL statewide)"},
            {"year": 1960, "name": "Hurricane Donna", "type": "Major Hurricane",
             "description": "Category 4 at FL Keys landfall, produced catastrophic surge of 10–15 ft across SW Florida Gulf coast. Benchmark historical event for regional surge risk.",
             "damage": "$900M (1960 dollars)"},
        ],
        flood_history_note  = (
            "NFIP claims data for zip code 33931 reflect 2,847 paid claims totaling over $312 million — "
            "the vast majority resulting from Hurricane Ian's catastrophic 2022 landfall. This represents "
            "one of the highest NFIP claim concentrations per capita of any zip code in the country. "
            "High tide flooding at the Fort Myers gauge is currently minimal (3 days/year) due to the "
            "Gulf's microtidal character, but is projected to rise to 25–60 days annually by 2050 under "
            "the intermediate scenario. The repetitive loss designation for many island properties "
            "significantly affects NFIP eligibility and premium levels."
        ),
        insurance_requirement       = "Mandatory",
        insurance_requirement_detail= "Required for all federally-backed mortgages on properties in Zone VE. Applies at closing and must be maintained continuously.",
        estimated_nfip_premium      = "$8,000–$18,000/year",
        nfip_premium_note           = (
            "Estimated range for a residential structure in Zone VE under NFIP Risk Rating 2.0, "
            "post-Ian market conditions. Actual premium depends on structure elevation, construction "
            "type, and coverage amount. Risk Rating 2.0 is moving VE zone premiums toward full "
            "actuarial cost, and rates are increasing annually with no cap for new policies."
        ),
        private_market_status       = "Severely Limited / Market in Crisis",
        private_market_note         = (
            "Heritage Insurance exited Florida (2023). Farmers, Bankers Insurance, and multiple "
            "admitted carriers have suspended or sharply reduced Gulf Coast exposure. Citizens "
            "Property Insurance (state-backed insurer of last resort) is now the primary market "
            "for most Fort Myers Beach properties. Private surplus lines available at significantly "
            "elevated premiums. Buyers should budget for Citizens coverage and expect continued "
            "deterioration of the private market."
        ),
        state_disclosure            = "Required",
        state_disclosure_detail     = (
            "Florida law requires sellers to disclose known flood history, including NFIP claims "
            "and repetitive loss designations, in the FREC-mandated disclosure form. Post-Ian "
            "properties with documented damage must disclose scope of damage and repairs completed."
        ),
        regulatory_note             = (
            "Fort Myers Beach adopted an updated Comprehensive Resilience Plan following Hurricane Ian "
            "with enhanced elevation requirements for all reconstruction. The Florida Coastal Construction "
            "Control Line (CCCL) applies to this property; any construction or substantial improvement "
            "requires a CCCL permit from the Florida Department of Environmental Protection (DEP). "
            "FEMA's ongoing FIRM remapping of Lee County may result in revised BFE or zone designations "
            "affecting this parcel. Development decisions should include a full CCCL permitting review "
            "and assessment of pending map revisions before committing capital."
        ),
        recommendations     = [
            {"title": "Verify FEMA Map Revision Status Before Any Commitment",
             "description": (
                "Lee County FIRM panels are under active revision following Hurricane Ian. Preliminary "
                "maps may show different BFE or zone boundaries than current effective maps. Any "
                "development or investment decision should include a current Letter of Map Determination "
                "(LOMD) request and a review of preliminary FIRM panels for the affected panel."
             )},
            {"title": "Design to Minimum 2–3 Feet of Freeboard Above Current BFE",
             "description": (
                "Fort Myers Beach post-Ian reconstruction guidelines recommend elevated construction "
                "significantly above BFE. Given the island's Ian-validated surge profile and projected "
                "BFE increases from map revision, designing to 16–17 ft NAVD88 minimum finished floor "
                "elevation provides meaningful resilience against the next major hurricane event."
             )},
            {"title": "Plan for Citizens Insurance and Understand Policy Limitations",
             "description": (
                "Citizens Property Insurance is likely the only viable market for this property. "
                "Citizens flood coverage is capped at $500,000 for structures and does not include "
                "contents or additional living expenses. Buyers requiring coverage above these limits "
                "must seek surplus lines markets. Budget $10,000–$20,000+/year for combined wind and flood."
             )},
            {"title": "Evaluate Hurricane-Resistant Construction Standards",
             "description": (
                "Florida Building Code Chapter 16 (High-Velocity Hurricane Zone) applies to Lee County. "
                "New construction should use impact-resistant windows and doors, reinforced concrete "
                "or engineered wood framing, and metal roofing with rated fasteners. Breakaway walls "
                "required for all enclosed spaces below BFE. Consider whole-structure elevations "
                "significantly above BFE minimum."
             )},
            {"title": "Assess Evacuation Zone and Plan Accordingly",
             "description": (
                "Estero Island is in Lee County Evacuation Zone A — the highest-priority zone for "
                "mandatory evacuation orders. The single-causeway access creates a critical time "
                "constraint: evacuation typically must begin 36–48 hours before landfall for safe "
                "egress. Buyers and tenants must understand that this property may be uninhabitable "
                "for extended periods following major hurricane events."
             )},
            {"title": "Obtain a Detailed Elevation Certificate Before Closing",
             "description": (
                "An Elevation Certificate documenting the structure's finished floor elevation "
                "relative to BFE is essential for accurate NFIP rating and should be obtained "
                "prior to any purchase or refinancing. For post-Ian rebuilt structures, verify "
                "that the EC reflects the as-built reconstruction elevation."
             )},
        ],
    )


@app.route("/RiskReport/Malibu")
def risk_report_malibu():
    return render_template("RiskReport_Malibu.html",
        client_name         = "Sample Report — CoastalRisk",
        address             = "22000 Pacific Coast Hwy, Malibu, CA 90265",
        date                = "April 2026",
        year                = "2026",
        latitude            = "34.0259",
        longitude           = "118.7798",
        overall_risk        = "High",
        exec_summary        = (
            "This property on Pacific Coast Highway in Malibu, California occupies a beachfront parcel "
            "in FEMA Zone AE with a Base Flood Elevation of 12 ft NAVD88. Unlike Gulf and Atlantic coast "
            "properties, Pacific coast risk is not driven by hurricane storm surge — it is shaped instead "
            "by El Niño-driven winter storm wave runup, chronic coastal erosion, and long-term sea level "
            "rise. The 1982–83 and 1997–98 El Niño events demonstrated that severe PCH flooding can "
            "destroy or severely damage beachfront structures, and more frequent and intense atmospheric "
            "river events are projected under climate change. The Los Angeles tide gauge shows a local "
            "sea level rise rate of 1.54 mm/year, with NOAA projecting 1.1 feet of additional rise "
            "under the intermediate scenario by 2050. The California insurance market has experienced "
            "significant carrier withdrawals, with State Farm and Allstate both exiting California "
            "homeowners coverage in 2023. The California Coastal Commission exercises strict permitting "
            "authority over all development and reconstruction on this parcel. While this property's "
            "surge risk profile is materially different from — and in some respects lower than — Gulf "
            "and Atlantic coastal properties, erosion, wave action, and insurance access are near-term, "
            "material concerns for any long-term investment."
        ),
        distance_to_shore   = "Direct beachfront — 0 feet to Pacific Ocean shoreline",
        coastal_region      = "Southern California Coast — Los Angeles County / Malibu",
        location_context    = (
            "This property is located on Pacific Coast Highway in Malibu, one of the most iconic "
            "and risk-exposed beachfront corridors in California. PCH beachfront parcels sit directly "
            "on a narrow sand beach with no setback from the ocean. The Pacific coast's risk profile "
            "differs fundamentally from the Atlantic and Gulf: there is no hurricane threat, but "
            "extratropical winter storms — amplified during El Niño years — produce significant wave "
            "runup, sand loss, and structural damage. The narrow beach in this section of Malibu has "
            "experienced chronic erosion, and in some El Niño winters, waves reach PCH directly. "
            "The nearest NOAA tide gauge is located at Los Angeles (Santa Monica), CA (Station 9410660), "
            "approximately 20 miles southeast. California coastal bluffs further north on this coast "
            "face additional erosion and failure risks not applicable to this beach-level parcel."
        ),
        geomorphology_type  = "Sandy Beach — Direct Ocean Frontage / Low Backshore",
        geomorphology_rating= "High",
        geomorphology_note  = (
            "Narrow sandy beach with very limited sediment supply from the Santa Monica Mountains "
            "drainage system. The beach in this section of Malibu is classified as a sediment-deficit "
            "environment, meaning natural beach replenishment does not offset erosive wave energy. "
            "El Niño winters characteristically strip significant volumes of sand from PCH beachfront "
            "properties, leaving structures directly exposed to wave impact."
        ),
        flood_zone          = "AE",
        sfha                = True,
        sfha_label          = "Special Flood Hazard Area",
        base_flood_elevation= "12 ft NAVD88",
        mandatory_insurance = True,
        nfip_community_name = "City of Malibu, CA (CID: 060043)",
        nfip_crs_rating     = "Class 9 — 5% NFIP premium discount",
        annual_flood_chance = "1% annual chance (100-year flood); 26% chance over 30-year mortgage",
        fema_note           = (
            "Zone AE designates a 1% annual chance flood zone with a defined Base Flood Elevation, "
            "indicating significant flood risk driven in this case by Pacific storm wave runup and "
            "coastal flooding rather than hurricane surge. Unlike Zone VE, AE does not require wave "
            "action engineering, but beachfront AE properties in Malibu are effectively exposed to "
            "wave impact during severe El Niño events. Mandatory flood insurance applies for all "
            "federally-backed mortgages. The City of Malibu participates in the Community Rating "
            "System at Class 9, providing a modest 5% premium discount. FIRM panels for this area "
            "are subject to periodic revision as coastal conditions change."
        ),
        slr_tide_gauge      = "Los Angeles (Santa Monica), CA (NOAA Station 9410660)",
        slr_rate_local      = "1.54",
        slr_gauge_period    = "Based on 1924–2023 tide gauge record (NOAA CO-OPS)",
        slr_low_2030        = "0.1",
        slr_low_2050        = "0.3",
        slr_low_2075        = "0.5",
        slr_low_2100        = "0.8",
        slr_intermediate_2030 = "0.2",
        slr_intermediate_2050 = "1.1",
        slr_intermediate_2075 = "2.0",
        slr_intermediate_2100 = "3.3",
        slr_high_2030       = "0.3",
        slr_high_2050       = "0.9",
        slr_high_2075       = "2.4",
        slr_high_2100       = "4.9",
        sea_level_intro     = (
            "The Los Angeles tide gauge has recorded a local relative sea level rise rate of 1.54 mm/year "
            "since 1924 — lower than Atlantic coast rates, reflecting Southern California's more stable "
            "tectonic setting. Under NOAA's 2022 intermediate planning scenario, Southern California will "
            "experience approximately 1.1 feet of additional sea level by 2050. This matters more for "
            "beachfront properties than might be expected: even modest sea level increases elevate the "
            "baseline from which storm waves operate, increasing effective wave runup and inundation "
            "extent during El Niño events. California state coastal planning guidance requires SLR "
            "resilience analysis for all new Coastal Commission permit applications."
        ),
        property_note       = (
            "At this parcel's beach-level elevation, the intermediate SLR scenario combined with "
            "projected increases in Pacific storm intensity suggests meaningfully higher wave runup "
            "frequencies by mid-century. The beach buffer in front of this structure — already "
            "narrowed by erosion — is likely to continue retreating. Development decisions should "
            "consider both the structural and regulatory implications of a shrinking beach buffer "
            "under California Coastal Commission jurisdiction."
        ),
        cat1_surge          = 2,
        cat2_surge          = 3,
        cat3_surge          = 5,
        cat4_surge          = 6,
        cat5_surge          = 8,
        storm_surge_intro   = (
            "Pacific Coast Highway beachfront properties are not subject to hurricane storm surge. "
            "Instead, coastal flooding risk is driven by extratropical winter storms and El Niño events, "
            "which produce wave runup and elevated sea levels that can reach and overtop PCH. The figures "
            "below represent estimated total coastal water levels (storm surge + wave runup) for storm "
            "events of increasing intensity, based on historical El Niño event records and NOAA coastal "
            "flood data for the Southern California coast. The 1982–83 and 1997–98 El Niño winters are "
            "the benchmark severe events for this location."
        ),
        storm_surge_property_note = (
            "Historical PCH flooding during the 1982–83 El Niño caused direct wave impact on structures "
            "and temporary road closures lasting weeks. The 1997–98 El Niño produced similar conditions. "
            "Both events involved total coastal water levels in the 4–6 ft above MHHW range, consistent "
            "with the 'Severe El Niño' scenario in the table above. With 1.1 ft of additional sea level "
            "rise by 2050, equivalent storm events would produce proportionally greater inundation extent, "
            "reducing the return period of historically destructive El Niño flood levels."
        ),
        erosion_rate        = "–0.3 to –0.5 m/year (net beach retreat)",
        erosion_rating      = "High",
        erosion_note        = (
            "PCH beachfront properties in this section of Malibu have experienced consistent net beach "
            "erosion. El Niño winters characteristically accelerate erosion dramatically; beach profiles "
            "can retreat 10–20 meters during a single severe season. Sand recovery between El Niño "
            "events is typically incomplete, producing a long-term net retreat trend."
        ),
        sea_level_rate      = "+1.54 mm/year (relative, LA gauge)",
        sea_level_rating    = "Moderate",
        sea_level_note      = (
            "Southern California's SLR rate is lower than Atlantic and Gulf coast equivalents, "
            "but is accelerating and is expected to increase in coming decades as global ice sheet "
            "loss compounds ocean thermal expansion."
        ),
        tidal_range         = "4.5 ft mean tidal range (low mesotidal)",
        tidal_rating        = "Moderate",
        tidal_note          = (
            "Southern California's moderate tidal range means king tide events (highest predicted tides) "
            "can produce 1.5–2 ft of additional water level above mean higher high water, amplifying "
            "wave runup during coincident storm events. King tide and El Niño storm coincidence is the "
            "highest-impact coastal scenario for this location."
        ),
        wave_height         = "Significant wave height 1.5–2.5 m typical; 5–7 m during El Niño storms",
        wave_rating         = "High",
        wave_note           = (
            "The Pacific Ocean delivers persistent swell energy year-round, with dramatically elevated "
            "wave heights during El Niño winters. Severe El Niño swell events can produce wave heights "
            "exceeding 20 ft offshore and significant runup onto PCH beachfront structures."
        ),
        slope_pct           = "< 0.3% coastal slope (flat beach / backshore profile)",
        slope_rating        = "High",
        slope_note          = (
            "The flat beach profile and minimal backshore elevation mean that elevated wave runup "
            "during storm events rapidly reaches and can overtop the coastal highway and structure "
            "foundations, with limited natural attenuation."
        ),
        nfip_zip            = "90265",
        nfip_claims_count   = "312",
        nfip_claims_total   = "$18.7M",
        htf_days_current    = "3",
        htf_days_2050       = "20–45",
        flood_events        = [
            {"year": 1983, "name": "1982–83 El Niño Winter Storms", "type": "Extratropical Storm Series",
             "description": "One of the most severe El Niño seasons on record. Repeated storm wave events overwashed PCH beachfront properties in Malibu. Multiple structures damaged or destroyed. PCH closed for extended periods due to wave overwash and road damage.",
             "damage": "~$500M (CA coastal, 1983 dollars)"},
            {"year": 1998, "name": "1997–98 El Niño Winter Storms", "type": "Extratropical Storm Series",
             "description": "Second major El Niño event in 15 years. Severe wave runup and coastal flooding along PCH corridor. Significant sand loss from Malibu beaches. PCH road closures and structural damage to beachfront properties.",
             "damage": "~$1.1B (CA coastal)"},
            {"year": 2016, "name": "2015–16 El Niño Coastal Flooding", "type": "Coastal Storm Event",
             "description": "Moderate-to-strong El Niño produced multiple high wave events and elevated water levels along PCH. Coastal road damage and erosion acceleration observed throughout Malibu. Repeat of pattern from 1983 and 1998 events.",
             "damage": "$300M+ (CA coastal)"},
            {"year": 2023, "name": "Atmospheric River Flooding Series", "type": "Extreme Precipitation Event",
             "description": "Repeated atmospheric river events produced record coastal and inland flooding. PCH experienced multiple closures. Malibu canyon fires in prior years left watersheds unstable, amplifying mudflow and sediment discharge to coast.",
             "damage": "$30B+ (CA statewide)"},
            {"year": 2025, "name": "Palisades Wildfire — Coastal Watershed Impact", "type": "Wildfire / Secondary Flood Risk",
             "description": "The January 2025 Palisades Fire burned significant area in the coastal watersheds draining to PCH. Burned watersheds produce dramatically increased post-fire debris flow and stormwater runoff risk for 3–5 years following fire, amplifying coastal flood hazard.",
             "damage": "$30B+ (Palisades Fire total)"},
        ],
        flood_history_note  = (
            "NFIP claims data for zip code 90265 reflect 312 paid claims totaling $18.7 million — "
            "substantially lower than Gulf and Atlantic coast equivalents, in part because many high-value "
            "Malibu properties carry private insurance or self-insure rather than NFIP, and in part "
            "because Pacific coast flood events are less frequent than Atlantic hurricane impacts. "
            "However, when El Niño events do produce coastal flooding, the concentrated value of PCH "
            "beachfront structures means damages can be severe. High tide flooding at the LA gauge "
            "currently occurs approximately 3 days/year; the intermediate scenario projects this rising "
            "to 20–45 days annually by 2050, a meaningful increase for direct-beachfront properties."
        ),
        insurance_requirement       = "Mandatory",
        insurance_requirement_detail= "Required for all federally-backed mortgages on properties in Zone AE. Applies at closing and must be maintained continuously.",
        estimated_nfip_premium      = "$3,000–$8,000/year",
        nfip_premium_note           = (
            "Estimated range for a residential structure in Zone AE under NFIP Risk Rating 2.0. "
            "Actual premium depends on elevation above BFE, construction type, and coverage amount. "
            "Note: many Malibu beachfront properties carry private flood insurance or are self-insured "
            "due to the high structure values and NFIP coverage caps ($250,000 structural maximum)."
        ),
        private_market_status       = "Severely Restricted — Market Withdrawal in Progress",
        private_market_note         = (
            "State Farm announced withdrawal from new California homeowners policies in May 2023. "
            "Allstate ceased writing new California policies in 2022. Several additional carriers "
            "have non-renewed coastal Malibu policies following the Woolsey and Palisades fires. "
            "The California FAIR Plan (state-backed insurer of last resort) now covers significant "
            "numbers of Malibu properties but provides limited coverage ($3M max, no contents). "
            "Surplus lines markets remain available at significantly elevated premiums."
        ),
        state_disclosure            = "Required",
        state_disclosure_detail     = (
            "California requires the Natural Hazard Disclosure Statement (NHD) and Transfer "
            "Disclosure Statement (TDS) for all residential real estate transactions. The NHD must "
            "disclose Special Flood Hazard Area designation, dam inundation zones, and known "
            "geological hazards. Wildfire Hazard Severity Zone designation must also be disclosed."
        ),
        regulatory_note             = (
            "All development, reconstruction, and substantial improvement on this parcel requires "
            "a Coastal Development Permit (CDP) from the California Coastal Commission (CCC). "
            "The CCC applies strict sea level rise resilience standards to all new development, "
            "and is increasingly conditioning permits on managed retreat assessments for "
            "beachfront properties. CEQA review is required for significant projects. The City "
            "of Malibu's Local Coastal Program (LCP) adds additional setback and design "
            "requirements beyond state minimums. Buyers should obtain a full CCC and LCP "
            "permitting review before any development or major renovation commitment, as "
            "permit denial risk for beachfront reconstruction is materially elevated "
            "compared to inland locations."
        ),
        recommendations     = [
            {"title": "Obtain a California Coastal Commission Pre-Application Consultation",
             "description": (
                "Before committing to any development, renovation, or substantial improvement, "
                "schedule a pre-application meeting with the California Coastal Commission. "
                "CCC staff can identify current sea level rise policies, setback requirements, "
                "and permit conditions likely to apply to this parcel. Permit denial risk is "
                "real and material for beachfront properties in the current regulatory environment."
             )},
            {"title": "Commission a Site-Specific Coastal Erosion Assessment",
             "description": (
                "Engage a licensed coastal geomorphologist to assess the current rate of beach "
                "retreat at this specific parcel, including El Niño-cycle dynamics and post-fire "
                "watershed effects. This assessment is typically required for CCC permit applications "
                "and provides essential data for planning finished floor elevation and setback design."
             )},
            {"title": "Evaluate FAIR Plan Coverage Against Surplus Lines Alternatives",
             "description": (
                "With State Farm and Allstate withdrawn from California, the insurance solution for "
                "this property likely involves a combination of NFIP flood coverage, FAIR Plan fire "
                "and wind coverage, and potentially Lloyd's or other surplus lines markets for "
                "comprehensive protection. Obtain quotes from a California surplus lines broker "
                "experienced in high-value coastal and wildfire-exposed properties."
             )},
            {"title": "Design for Wave Impact, Not Just Flood Inundation",
             "description": (
                "PCH beachfront structures face wave impact forces during severe El Niño events "
                "that are distinct from inundation flooding. Structural design should consider "
                "wave pressure loads on the ocean-facing facade, foundation scour from wave "
                "action, and debris impact. A licensed structural engineer experienced in "
                "Pacific coastal construction should review any new or reconstructed structure."
             )},
            {"title": "Monitor Post-Palisades Fire Debris Flow Risk for 3–5 Years",
             "description": (
                "The 2025 Palisades Fire burned coastal watersheds that drain to PCH in the "
                "Malibu area. Burned watersheds produce dramatically elevated debris flow and "
                "mudslide risk for 3–5 years following fire, particularly during the first "
                "major rain season. Monitor LA County debris flow warnings and confirm that "
                "any drainage systems serving this parcel are clear and functional."
             )},
        ],
    )


@app.route("/success")
def success():
    return render_template("success.html")


def find_closest_feature(lng, lat):
    closest_feature = None
    closest_distance = float('inf')
    try:
        for feature in geojson_data['features']:
            if feature['geometry']['type'] == 'MultiLineString':
                for line in feature['geometry']['coordinates']:
                    for coordinate_pair in line:
                        try:
                            feature_lng, feature_lat = coordinate_pair
                            distance = haversine((lat, lng), (feature_lat, feature_lng), unit=Unit.MILES)
                            if distance < closest_distance:
                                closest_distance = distance
                                closest_feature = feature
                        except ValueError as e:
                            print(f"Error unpacking coordinates: {coordinate_pair} - {e}")

        if closest_distance >= 20:
            return jsonify({"Your location is too far from the coast."}), 404
        return closest_feature
    except Exception as e:
        print(f"Error finding closest feature: {e}")
        return None


def get_feature_lat_lng(lng, lat):
    closest_feature_lat = None
    closest_feature_lng = None
    closest_distance = float('inf')
    for feature in geojson_data['features']:
        
        if feature['geometry']['type'] == 'MultiLineString':
            
            for line in feature['geometry']['coordinates']:
               
                for coordinate_pair in line:
                    try:
                        feature_lng, feature_lat = coordinate_pair
                        
                        distance = haversine((lat, lng), (feature_lat, feature_lng), unit=Unit.MILES)
                        
                        
                        if distance < closest_distance:
                            closest_distance = distance
                            closest_feature_lat = feature_lat
                            closest_feature_lng = feature_lng
                    except ValueError as e:
                        print(f"Error unpacking coordinates: {coordinate_pair} - {e}")
    
    
    return closest_feature_lat, closest_feature_lng


def get_coastal_data_from_feature(feature):
    if feature is None:
        return None
    try:
        properties = feature['properties']
        return {
            'cvi': properties.get('CVI'),
            'erosion': properties.get('EROSION'),
            'sea_level': properties.get('SEA_LEVEL'),
            'tides': properties.get('TIDES'),
            'geomorphology': properties.get('GEOMORPH'),
            'waves': properties.get('WAVES'),
            'slope': properties.get('SLOPE')


        }
    except Exception as e:
        print(f"Error getting coastal data from feature: {e}")
        return None
    

if __name__ == '__main__':
    app.run(debug=True, port=5001)