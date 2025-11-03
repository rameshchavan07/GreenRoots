from eoms import app
from flask import jsonify, request, render_template
from eoms.model.store import get_all_active_stores
from eoms.model.addres_utils import filter_nearby_stores, calculate_distance
from geopy.geocoders import Nominatim

# ---------------------------
#  STORE ROUTES – INDIA
# ---------------------------

# Route to show all stores
@app.route('/stores')
def view_stores():
    all_stores = get_all_active_stores()
    return render_template('/shopping/store_list.html', stores=all_stores)


# Route to return stores as JSON (based on search query or coordinates)
@app.route('/stores/json')
def get_stores_json():
    search_query = request.args.get('search', '')
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    # Initialize geocoder for India
    geolocator = Nominatim(user_agent="agrihire_app")

    # If user provided a search query (like "Mumbai"), convert to coordinates
    location = None
    if search_query:
        try:
            location = geolocator.geocode(f"{search_query}, India")
        except Exception as e:
            print("Geocoding error:", e)

    # Extract latitude and longitude
    if lat and lon:
        lat, lon = float(lat), float(lon)
    elif location:
        lat, lon = location.latitude, location.longitude
    else:
        return jsonify({'error': 'Location not found'}), 404

    # Fetch all stores and filter nearby ones
    all_stores = get_all_active_stores()
    nearby_stores = filter_nearby_stores(all_stores, lat, lon)

    # Calculate distance (in km)
    for store in nearby_stores:
        store_lat = store['lat']
        store_lon = store['lng']
        store['distance'] = calculate_distance(lat, lon, store_lat, store_lon)

    # Sort by distance
    nearby_stores.sort(key=lambda x: x['distance'])
    return jsonify(nearby_stores)


# Route to search postal code using Indian data
@app.route('/stores/post_code', methods=['GET'])
def search_post_code():
    """
    For India, we will use Nominatim (OpenStreetMap) instead of Addy API.
    Example: /stores/post_code?q=110001
    """
    query = request.args.get('q')
    if not query:
        return jsonify({'error': 'Missing query parameter'}), 400

    geolocator = Nominatim(user_agent="agrihire_app")
    try:
        location = geolocator.geocode(f"{query}, India")
        if location:
            return jsonify({
                'post_code': query,
                'lat': location.latitude,
                'lon': location.longitude,
                'address': location.address
            })
        else:
            return jsonify({'error': 'Postcode not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Error fetching data: {str(e)}'}), 500
