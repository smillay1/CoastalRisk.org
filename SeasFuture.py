from flask import Flask, render_template, request, jsonify, url_for
from flask_cors import CORS
import os
import requests
import json
from haversine import haversine, Unit
import urllib.parse

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["https://coastalrisk.org", "https://66e41117e86395fce4b28e7e--magnificent-melomakarona-e43288.netlify.app"]}})

# Load GeoJSON data
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



# Load environment variables
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
        # Fetching user input
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
                if closest_feature:
                    coastal_vulnerability_data = get_coastal_data_from_feature(closest_feature)
                    return render_template('results.html', address=address, results=coastal_vulnerability_data, latitude=latitude, longitude=longitude)
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
    
@app.route('/donate')
def donate():
    return render_template('donate.html')


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





# import numpy as np
# import pandas as pd
# import netCDF4 as nc
# from netCDF4 import Dataset
# from geopy.distance import distance
# import cftime
# from cftime import num2date
# from geopy.geocoders import Nominatim
# from geopy.exc import GeocoderTimedOut
# from pyproj import Proj, transform, Transformer
# import cartopy.crs as ccrs




#load .nc file
# def load_netcdf():
#     try:
#         data = nc.Dataset('temp.nc')
#         print("NetCDF file loaded successfully")
#         return data
#     except Exception as e:
#         print(f"Error loading NetCDF file: {str(e)}")
#         return None

# netcdf_data = load_netcdf()
# print(netcdf_data.__dict__)


# target_years = np.arange(2020, 2100, 10)

# def get_lat_lon_from_address(address):
#     geolocator = Nominatim(user_agent="climate_app")
#     try:
#         location = geolocator.geocode(address, timeout=10)
#         if location:
#             lat, lon = location.latitude, location.longitude
#             print(f"Coordinates for {address}: Latitude = {lat}, Longitude = {lon}")
#             return lat, lon
#         else:
#             print(f"Could not find location for {address}")
#             return None, None
#     except GeocoderTimedOut:
#         print(f"Geocoder timed out for {address}")
#         return None, None


# def extract_years_from_netcdf(netcdf_data):
    
#     try:
        # Extract the time variable
#         time = netcdf_data.variables['time'][:]
#         time_units = netcdf_data.variables['time'].units
#         time_calendar = netcdf_data.variables['time'].calendar if 'calendar' in netcdf_data.variables['time'].ncattrs() else 'standard'
        
#         print("Time data shape:", time.shape)
#         print("Time units:", time_units)
#         print("Time calendar:", time_calendar)
        
#         # Convert the time variable to datetime
#         time_dt = cftime.num2date(time, time_units, calendar=time_calendar)
#         print("Converted time data (first 5):", time_dt[:5])
#         print("Converted time data (last 5):", time_dt[-5:])
        
#         # Convert datetime to pandas datetime and extract the years
#         time_years = pd.Series(time_dt).apply(lambda x: x.year if pd.notnull(x) else np.nan)
#         print("Extracted years (first 10):", time_years[:10])
        
#         # Filter out any NaN values
#         valid_years = time_years.dropna().unique()
#         print("Valid years:", valid_years)
        
#         return valid_years, time_years
#     except Exception as e:
# #         print(f"Error extracting years from NetCDF data: {str(e)}")
# #         return None, None

# # # Adjust the longitude to the 0-360 range if needed
# def adjust_longitude(lon):
#     if lon < 0:
#         lon = 360 + lon  # Shift longitude to 0-360 range
#     return lon

# # Define WGS84 (EPSG:4326) as the input projection
# geo_proj = Proj(init='epsg:4326')

# # Define the rotated pole projection explicitly
# rotated_proj = Proj(proj='ob_tran', o_proj='latlong', o_lat_p=42.5, o_lon_p=83.0)

# def convert_to_rotated_coords(lat, lon):
#     lon = adjust_longitude(lon)
#     rlat, rlon = transform(geo_proj, rotated_proj, lon, lat)
#     return rlat, rlon


# # Example usage in your temperature extraction function
# def get_temperature_data(netCDF_data, target_years, target_lat, target_lon):
#     try:
#         # Load rotated lat, lon, and temperature data
#         rlat_data = netCDF_data.variables['rlat'][:]
#         rlon_data = netCDF_data.variables['rlon'][:]
#         temp = netCDF_data.variables['tas'][:]  # 'tas' is near-surface temperature

#         print(f"rlat values: {rlat_data[:5]}")
#         print(f"rlon values: {rlon_data[:5]}")

#         # Adjust target longitude to 0-360 range
#         target_lon = adjust_longitude(target_lon)
#         print(f"Adjusted Longitude: {target_lon}")

#         # Find the nearest grid point without transformation
#         lat_idx, lon_idx = get_nearest_rotated_grid_point(rlat_data, rlon_data, target_lat, target_lon)
#         print(f"Nearest grid point without transformation: Lat index = {lat_idx}, Lon index = {lon_idx}")

#         valid_years, time_years = extract_years_from_netcdf(netCDF_data)
#         temp_units = netCDF_data.variables['tas'].units
#         print(f"Temperature units: {temp_units}")

#         # Convert the input lat/lon to rotated coordinates
#         target_rlat, target_rlon = convert_to_rotated_coords(target_lat, target_lon)
#         print(f"Converted to rotated grid: target_rlat = {target_rlat}, target_rlon = {target_rlon}")

#         # Find the nearest grid point based on rotated lat/lon
#         lat_idx, lon_idx = get_nearest_rotated_grid_point(rlat_data, rlon_data, target_rlat, target_rlon)
#         print(f"Nearest grid point: Rotated lat index = {lat_idx}, Rotated lon index = {lon_idx}")

#         temp_data = []

#         for year in target_years:
#             if year in valid_years:
#                 year_index = np.where(time_years == year)[0][0]
#                 year_temp = temp[year_index, lat_idx, lon_idx]  # Temperature for that year and location

#                 # Convert from Kelvin to Fahrenheit
#                 avg_temp_f = (year_temp - 273.15) * 9/5 + 32
#                 print(f"Converted temperature (F) for year {year}: {avg_temp_f}")

#                 temp_data.append({'year': year, 'temperature': avg_temp_f})
#             else:
#                 temp_data.append({'year': year, 'temperature': np.nan})

#         return temp_data
#     except Exception as e:
#         print(f"Error processing temperature data: {str(e)}")
#         return None

# def get_nearest_rotated_grid_point(rlatitudes, rlongitudes, target_rlat, target_rlon):
#     lat_diff = np.abs(rlatitudes - target_rlat)
#     lon_diff = np.abs(rlongitudes - target_rlon)

#     print(f"Target rotated lat/lon: {target_rlat}, {target_rlon}")
#     print(f"Grid lat diffs (min): {lat_diff.min()}, Grid lon diffs (min): {lon_diff.min()}")

#     nearest_lat_idx = lat_diff.argmin()  # Get the index of the nearest rotated latitude
#     nearest_lon_idx = lon_diff.argmin()  # Get the index of the nearest rotated longitude

#     print(f"Nearest lat index: {nearest_lat_idx}, Nearest lon index: {nearest_lon_idx}")
#     return nearest_lat_idx, nearest_lon_idx



# # Check if the 'rotated_pole' variable exists in the NetCDF dataset
# if 'rotated_pole' in netcdf_data.variables:
#     rotated_pole_info = netcdf_data.variables['rotated_pole']
#     print(f"Rotated pole information: {rotated_pole_info}")
#     print(rotated_pole_info.__dict__)  # Print the attributes of the rotated pole
# else:
#     print("Rotated pole information not found in variables.")
    


# Flask:
 # elif data_type == 'Temperature':
                #     lat, lon = get_lat_lon_from_address(address)
                #     temperature_data = get_temperature_data(netcdf_data, target_years, lat, lon)
                #     if temperature_data:
                #         return render_template('results.html', address=address, results={'temperature': temperature_data},
                #                        css_url=url_for('static', filename='styles.css'))
                #     else:
                #         abort(400, description="Invalid data type selected.")