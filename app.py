from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Airport mapping
airport_map = {
    ('Manila', 'Philippines'): 'MNL',
    ('Tokyo', 'Japan'): 'NRT',
    ('Seoul', 'Korea'): 'ICN',
    ('Hong Kong', 'Hong Kong, China'): 'HKG',
    ('Bangkok', 'Thailand'): 'BKK',
    ('Singapore', 'Singapore'): 'SIN',
    ('Sydney', 'Australia'): 'SYD',
    ('London', 'United Kingdom'): 'LHR',
    ('New York', 'United States'): 'JFK',
}

def get_airport_code(city, country):
    return airport_map.get((city, country))

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'CTL Flight Price Service', 
        'status': 'running',
        'endpoints': ['/health', '/api/getFlightPrice']
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'flight-price-api'})

@app.route('/api/getFlightPrice', methods=['GET'])
def get_flight_price():
    try:
        # Extract parameters
        departure_city = request.args.get('departureCity', 'Manila')
        destination_city = request.args.get('destinationCity', 'Tokyo')
        fare_class = request.args.get('fareClass', 'economy').lower()
        
        # Smart price estimates
        route_estimates = {
            ('Manila', 'Tokyo'): 650,
            ('Manila', 'Seoul'): 580,
            ('Manila', 'Hong Kong'): 300,
            ('Manila', 'Singapore'): 350,
            ('Manila', 'Bangkok'): 400,
            ('Manila', 'Sydney'): 800,
            ('Manila', 'London'): 1200,
            ('Manila', 'New York'): 1400,
            ('Tokyo', 'Manila'): 650,
            ('Seoul', 'Manila'): 580,
            ('Hong Kong', 'Manila'): 300,
            ('Singapore', 'Manila'): 350,
            ('Bangkok', 'Manila'): 400,
            ('Sydney', 'Manila'): 800,
            ('London', 'Manila'): 1200,
            ('New York', 'Manila'): 1400,
        }
        
        route = (departure_city, destination_city)
        price = route_estimates.get(route, 750)
        
        # Adjust for business class
        if fare_class == 'business':
            price = int(price * 2.5)
        elif fare_class == 'first':
            price = int(price * 4)
        
        return jsonify({
            'error': False,
            'price': price,
            'currency': 'USD',
            'source': 'estimated',
            'route': f"{departure_city} to {destination_city}",
            'fare_class': fare_class,
            'search_url': f"https://www.google.com/travel/flights?q=Flights%20from%20{departure_city}%20to%20{destination_city}"
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Error: {str(e)}',
            'price': 1500,
            'source': 'fallback'
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
