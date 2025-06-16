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
        # Try to import fast-flights
        try:
            from fast_flights import FlightData, Passengers, get_flights
            from datetime import datetime, timedelta
            use_real_data = True
        except ImportError:
            use_real_data = False
        
        # Extract parameters
        departure_city = request.args.get('departureCity', 'Manila')
        departure_country = request.args.get('departureCountry', 'Philippines')
        destination_city = request.args.get('destinationCity', 'Tokyo')
        destination_country = request.args.get('destinationCountry', 'Japan')
        target_date = request.args.get('targetDate')
        travel_days = int(request.args.get('travelDays', 7))
        fare_class = request.args.get('fareClass', 'economy').lower()
        
        if use_real_data and target_date:
            # Get airport codes
            from_airport = get_airport_code(departure_city, departure_country)
            to_airport = get_airport_code(destination_city, destination_country)
            
            if from_airport and to_airport:
                try:
                    # Parse date
                    departure_date = datetime.strptime(target_date, '%Y-%m-%d')
                    return_date = departure_date + timedelta(days=travel_days)
                    
                    # Create flight data
                    flight_data = [
                        FlightData(date=departure_date.strftime('%Y-%m-%d'), from_airport=from_airport, to_airport=to_airport),
                        FlightData(date=return_date.strftime('%Y-%m-%d'), from_airport=to_airport, to_airport=from_airport)
                    ]
                    
                    # Map fare class
                    seat_class = 'business' if fare_class == 'business' else 'economy'
                    
                    # Get real flights
                    passengers = Passengers(adults=1, children=0, infants_in_seat=0, infants_on_lap=0)
                    result = get_flights(
                        flight_data=flight_data,
                        trip="round-trip",
                        seat=seat_class,
                        passengers=passengers,
                        fetch_mode="fallback"
                    )
                    
                    if result and result.flights:
                        best_flight = result.flights[0]
                        
                        # Try to get real price
                        real_price = None
                        if hasattr(best_flight, 'price') and best_flight.price:
                            try:
                                if isinstance(best_flight.price, (int, float)):
                                    real_price = best_flight.price
                                elif isinstance(best_flight.price, str):
                                    clean_price = best_flight.price.replace('$', '').replace(',', '').strip()
                                    if clean_price.replace('.', '').isdigit():
                                        real_price = float(clean_price)
                            except:
                                pass
                        
                        if real_price:
                            return jsonify({
                                'error': False,
                                'price': real_price,
                                'currency': 'USD',
                                'flight_details': {
                                    'airline': getattr(best_flight, 'name', 'Unknown'),
                                    'duration': getattr(best_flight, 'duration', 'Unknown'),
                                    'stops': getattr(best_flight, 'stops', 'Unknown'),
                                    'departure': getattr(best_flight, 'departure', 'Unknown'),
                                    'arrival': getattr(best_flight, 'arrival', 'Unknown')
                                },
                                'source': 'real_google_flights',
                                'search_url': f"https://www.google.com/travel/flights?q=Flights%20from%20{from_airport}%20to%20{to_airport}"
                            })
                except Exception as e:
                    print(f"Fast-flights error: {str(e)}")
        
        # Fallback to intelligent estimates
        return get_estimated_price(departure_city, destination_city, fare_class)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return get_estimated_price(departure_city, destination_city, fare_class)

def get_estimated_price(departure_city, destination_city, fare_class):
    """Smart price estimates as fallback"""
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
    }
    
    route = (departure_city, destination_city)
    price = route_estimates.get(route, 750)
    
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
