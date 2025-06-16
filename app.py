from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Expanded airport mapping - covers most major cities
airport_map = {
    # Philippines
    ('Manila', 'Philippines'): 'MNL',
    ('Cebu', 'Philippines'): 'CEB',
    ('Davao', 'Philippines'): 'DVO',
    
    # Asia Pacific
    ('Tokyo', 'Japan'): 'NRT',
    ('Osaka', 'Japan'): 'KIX',
    ('Seoul', 'Korea'): 'ICN',
    ('Busan', 'Korea'): 'PUS',
    ('Beijing', 'China, People\'s Rep. of'): 'PEK',
    ('Shanghai', 'China, People\'s Rep. of'): 'PVG',
    ('Hong Kong', 'Hong Kong, China'): 'HKG',
    ('Taipei', 'Taipei, China'): 'TPE',
    ('Bangkok', 'Thailand'): 'BKK',
    ('Singapore', 'Singapore'): 'SIN',
    ('Kuala Lumpur', 'Malaysia'): 'KUL',
    ('Jakarta', 'Indonesia'): 'CGK',
    ('Denpasar (Bali)', 'Indonesia'): 'DPS',
    ('Ho Chi Minh', 'Viet Nam'): 'SGN',
    ('Hanoi', 'Viet Nam'): 'HAN',
    ('Mumbai', 'India'): 'BOM',
    ('New Delhi', 'India'): 'DEL',
    ('Bangalore', 'India'): 'BLR',
    ('Sydney', 'Australia'): 'SYD',
    ('Melbourne', 'Australia'): 'MEL',
    ('Brisbane', 'Australia'): 'BNE',
    
    # Middle East
    ('Dubai', 'United Arab Emirates'): 'DXB',
    ('Abu Dhabi', 'United Arab Emirates'): 'AUH',
    ('Doha', 'Qatar'): 'DOH',
    ('Riyadh', 'Saudi Arabia'): 'RUH',
    
    # Europe
    ('London', 'United Kingdom'): 'LHR',
    ('Paris', 'France'): 'CDG',
    ('Frankfurt', 'Germany'): 'FRA',
    ('Amsterdam', 'Netherlands'): 'AMS',
    ('Madrid', 'Spain'): 'MAD',
    ('Rome', 'Italy'): 'FCO',
    ('Zurich', 'Switzerland'): 'ZUR',
    ('Vienna', 'Austria'): 'VIE',
    
    # Americas
    ('New York', 'United States'): 'JFK',
    ('Los Angeles', 'United States'): 'LAX',
    ('San Francisco', 'United States'): 'SFO',
    ('Chicago', 'United States'): 'ORD',
    ('Miami', 'United States'): 'MIA',
    ('Toronto', 'Canada'): 'YYZ',
    ('Vancouver', 'Canada'): 'YVR',
    ('Mexico City', 'Mexico'): 'MEX',
    ('São Paulo', 'Brazil'): 'GRU',
    ('Buenos Aires', 'Argentina'): 'EZE',
}

def get_airport_code(city, country):
    """Convert city/country to airport codes"""
    return airport_map.get((city, country))

@app.route('/api/getFlightPrice', methods=['GET'])
def get_flight_price():
    try:
        # Import fast_flights here to catch import errors
        try:
            from fast_flights import FlightData, Passengers, get_flights
        except ImportError as e:
            return jsonify({
                'error': True, 
                'message': f'fast_flights library not available: {str(e)}', 
                'price': 1500
            }), 500
        
        # Extract parameters
        departure_city = request.args.get('departureCity')
        departure_country = request.args.get('departureCountry')
        destination_city = request.args.get('destinationCity')
        destination_country = request.args.get('destinationCountry')
        target_date = request.args.get('targetDate')
        travel_days = int(request.args.get('travelDays', 1))
        fare_class = request.args.get('fareClass', 'economy').lower()
        num_people = int(request.args.get('numberOfPeople', 1))
        
        # Validate required parameters
        if not all([departure_city, departure_country, destination_city, destination_country, target_date]):
            return jsonify({'error': True, 'message': 'Missing required parameters'}), 400
        
        # Get airport codes
        from_airport = get_airport_code(departure_city, departure_country)
        to_airport = get_airport_code(destination_city, destination_country)
        
        if not from_airport or not to_airport:
            return jsonify({
                'error': True, 
                'message': f'Airport codes not found for {departure_city}/{departure_country} or {destination_city}/{destination_country}. Available cities: {list(set([city for city, country in airport_map.keys()]))}',
                'price': 1500
            }), 400
        
        # Parse dates
        from datetime import datetime, timedelta
        departure_date = datetime.strptime(target_date, '%Y-%m-%d')
        return_date = departure_date + timedelta(days=travel_days)
        
        # Map fare class
        seat_class_map = {
            'economy': 'economy',
            'business': 'business',
            'first': 'first'
        }
        seat_class = seat_class_map.get(fare_class, 'economy')
        
        # Determine trip type and flight data
        if travel_days > 0:
            # Round trip
            flight_data = [
                FlightData(date=departure_date.strftime('%Y-%m-%d'), from_airport=from_airport, to_airport=to_airport),
                FlightData(date=return_date.strftime('%Y-%m-%d'), from_airport=to_airport, to_airport=from_airport)
            ]
            trip = "round-trip"
        else:
            # One way
            flight_data = [
                FlightData(date=departure_date.strftime('%Y-%m-%d'), from_airport=from_airport, to_airport=to_airport)
            ]
            trip = "one-way"
        
        # Create passengers object
        passengers = Passengers(adults=num_people, children=0, infants_in_seat=0, infants_on_lap=0)
        
        # Get flights using fast-flights
        result = get_flights(
            flight_data=flight_data,
            trip=trip,
            seat=seat_class,
            passengers=passengers,
            fetch_mode="fallback"  # Use fallback for better reliability
        )
        
        # Extract price information
       if flights_with_prices:
    best_flight = min(flights_with_prices, key=lambda f: f.price)
    price = best_flight.price
    source = 'fast-flights'
else:
    # Use the first flight for details, but estimate the price
    best_flight = result.flights[0]
    
    # Smart price estimates based on routes
    route_prices = {
        ('MNL', 'NRT'): 650, ('MNL', 'ICN'): 580, ('MNL', 'HKG'): 300,
        ('MNL', 'SIN'): 350, ('MNL', 'BKK'): 400, ('MNL', 'KUL'): 380,
        ('MNL', 'SYD'): 800, ('MNL', 'MEL'): 850, ('MNL', 'LHR'): 1200,
        ('MNL', 'CDG'): 1250, ('MNL', 'LAX'): 1100, ('MNL', 'JFK'): 1400,
        ('NRT', 'MNL'): 650, ('ICN', 'MNL'): 580, ('HKG', 'MNL'): 300,
        ('SIN', 'MNL'): 350, ('BKK', 'MNL'): 400, ('KUL', 'MNL'): 380,
    }
    
    route = (from_airport, to_airport)
    price = route_prices.get(route, 750)  # Default to 750 if route not found
    
    # Adjust for business/first class
    if seat_class == 'business':
        price = int(price * 2.5)
    elif seat_class == 'first':
        price = int(price * 4)
    
    source = 'estimated_with_real_flight_data'

return jsonify({
    'error': False,
    'price': price,
    'currency': 'USD',
    'flight_details': {
        'airline': best_flight.name,
        'duration': best_flight.duration,
        'stops': best_flight.stops,
        'departure': best_flight.departure,
        'arrival': best_flight.arrival
    },
    'source': source,
    'search_url': f"https://www.google.com/travel/flights?q=Flights%20from%20{from_airport}%20to%20{to_airport}"
})
        else:
            return jsonify({'error': True, 'message': 'No flights found', 'price': 1500}), 404
            
    except Exception as e:
        print(f"Error in get_flight_price: {str(e)}")
        return jsonify({'error': True, 'message': f'Internal server error: {str(e)}', 'price': 1500}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'flight-price-api'})

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'CTL Flight Price Service', 
        'status': 'running',
        'endpoints': ['/health', '/api/getFlightPrice']
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
