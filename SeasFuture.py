from flask import Flask, render_template, request, jsonify, url_for
from flask_cors import CORS
import os
import requests
import json
from haversine import haversine, Unit
import urllib.parse

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["https://coastalrisk.org"]}})

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


@app.route("/premium")
def premium():
    return render_template("premium.html")

@app.route("/payment")
def premium():
    return render_template("payment.html")


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