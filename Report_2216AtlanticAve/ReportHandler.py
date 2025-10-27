from flask import Flask, render_template, redirect, url_for


app = Flask(__name__)

@app.route("/RiskReport")
def report():
    return render_template("RiskReport.html",
        client_name="Susan Burke",
        address="2216 Atlantic Ave, Sullivan’s Island, SC",
        date="May 15, 2025",
        year="2025",
        sea_level_risk="Moderate",
        sea_level_intro="In coming years, sea levels are expected to rise...",
        property_note="This property is likely to experience...",
        cat1_surge="Category 1 Storm Surge Depth: 2 feet",
        cat2_surge="Category 2 Storm Surge Depth: 6 feet",
        cat3_surge="Category 3 Storm Surge Depth: 10 feet",
        cat4_surge="Category 4 Storm Surge Depth: 14 feet",
        cat5_surge="Category 5 Storm Surge Depth: 17 feet",
        storm_surge_property_note="The property is at risk of storm surge flooding... Below you will find a storm surge simulation of a typical house. Move the slider left and right to get a visual idea of how the water level changes",
        # Flood zones go from lowest to highest: X, B, A, AE, V, VE
        flood_zone = "VE",
        flood_note = "This property is in FEMA’s highest flood classification level."
    )

@app.route('/unity')
def unity_sim():
    return redirect(url_for('static', filename='HouseWebBuild/index.html'))

if __name__ == "__main__":
    app.run(debug=True)