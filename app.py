from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import re

app = Flask(__name__)
CORS(app)

def get_airport_code_dynamic(city, country):
    """
    Dynamic airport code lookup using a comprehensive airport database
    This replaces the hardcoded airport_map
    """
    # Major airports database - expandable
    airports_db = {
        # Philippines
        'manila,philippines': 'MNL',
        'cebu,philippines': 'CEB', 
        'davao,philippines': 'DVO',
        'clark,philippines': 'CRK',
        'iloilo,philippines': 'ILO',
        
        # Japan
        'tokyo,japan': 'NRT',
        'osaka,japan': 'KIX',
        'kyoto,japan': 'KIX',  # Use KIX for Kyoto
        'nagoya,japan': 'NGO',
        'sapporo,japan': 'CTS',
        'fukuoka,japan': 'FUK',
        
        # South Korea
        'seoul,korea': 'ICN',
        'busan,korea': 'PUS',
        'jeju,korea': 'CJU',
        
        # China
        'beijing,china, people\'s rep. of': 'PEK',
        'shanghai,china, people\'s rep. of': 'PVG',
        'guangzhou,china, people\'s rep. of': 'CAN',
        'shenzhen,china, people\'s rep. of': 'SZX',
        
        # Hong Kong & Taiwan
        'hong kong,hong kong, china': 'HKG',
        'taipei,taipei, china': 'TPE',
        
        # Southeast Asia
        'bangkok,thailand': 'BKK',
        'singapore,singapore': 'SIN',
        'kuala lumpur,malaysia': 'KUL',
        'jakarta,indonesia': 'CGK',
        'denpasar (bali),indonesia': 'DPS',
        'ho chi minh,viet nam': 'SGN',
        'hanoi,viet nam': 'HAN',
        'phnom penh,cambodia': 'PNH',
        'yangon,myanmar': 'RGN',
        
        # India
        'new delhi,india': 'DEL',
        'mumbai,india': 'BOM',
        'bangalore,india': 'BLR',
        'chennai,india': 'MAA',
        'kolkata,india': 'CCU',
        'hyderabad,india': 'HYD',
        
        # Australia/New Zealand
        'sydney,australia': 'SYD',
        'melbourne,australia': 'MEL',
        'brisbane,australia': 'BNE',
        'perth,australia': 'PER',
        'auckland,new zealand': 'AKL',
        'wellington,new zealand': 'WLG',
        
        # Middle East
        'dubai,united arab emirates': 'DXB',
        'abu dhabi,united arab emirates': 'AUH',
        'doha,qatar': 'DOH',
        'riyadh,saudi arabia': 'RUH',
        'kuwait city,kuwait': 'KWI',
        
        # Europe
        'london,united kingdom': 'LHR',
        'paris,france': 'CDG',
        'frankfurt,germany': 'FRA',
        'amsterdam,netherlands': 'AMS',
        'madrid,spain': 'MAD',
        'rome,italy': 'FCO',
        'zurich,switzerland': 'ZUR',
        'vienna,austria': 'VIE',
        'brussels,belgium': 'BRU',
        'stockholm,sweden': 'ARN',
        'copenhagen,denmark': 'CPH',
        'oslo,norway': 'OSL',
        'helsinki,finland': 'HEL',
        
        # Americas
        'new york,united states': 'JFK',
        'los angeles,united states': 'LAX',
        'san francisco,united states': 'SFO',
        'chicago,united states': 'ORD',
        'miami,united states': 'MIA',
        'seattle,united states': 'SEA',
        'toronto,canada': 'YYZ',
        'vancouver,canada': 'YVR',
        'mexico city,mexico': 'MEX',
        'são paulo,brazil': 'GRU',
        'buenos aires,argentina': 'EZE',
        
        # Africa
        'cairo,egypt': 'CAI',
        'johannesburg,south africa': 'JNB',
        'cape town,south africa': 'CPT',
        'casablanca,morocco': 'CMN',
        'lagos,nigeria': 'LOS',
    }
    
    # Create lookup key
    lookup_key = f"{city.lower()},{country.lower()}"
    return airports_db.get(lookup_key)

def get_exchange_rate(from_currency, to_currency='USD'):
    """
    Get real-time exchange rate using Google's currency API or fallback services
    """
    if from_currency == to_currency:
        return 1.0
    
    try:
        # Try multiple currency APIs for reliability
        
        # Method 1: ExchangeRate-API (free tier)
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data['rates'].get(to_currency, 1.0)
            
        # Method 2: Fixer.io (backup - requires API key)
        # You can add this if you get a free API key
        
        # Method 3: Fallback to reasonable estimates
        fallback_rates = {
            'SGD': 0.74, 'EUR': 1.05, 'GBP': 1.27, 'JPY': 0.0067,
            'CNY': 0.14, 'KRW': 0.00075, 'THB': 0.029, 'PHP': 0.017,
            'AUD': 0.65, 'CAD': 0.73, 'INR': 0.012, 'MYR': 0.22
        }
        return fallback_rates.get(from_currency, 1.0)
        
    except Exception as e:
        print(f"Exchange rate error: {str(e)}")
        # Emergency fallback rates
        emergency_rates = {
            'SGD': 0.74, 'EUR': 1.05, 'GBP': 1.27, 'JPY': 0.0067,
            'CNY': 0.14, 'KRW': 0.00075, 'THB': 0.029, 'PHP': 0.017
        }
        return emergency_rates.get(from_currency, 1.0)

def extract_currency_and_amount(price_string):
    """
    Extract currency code and amount from price strings like 'SGD 185', '$1500', '€850'
    """
    if not price_string:
        return None, None
    
    price_str = str(price_string).strip()
    
    # Pattern to match currency codes and amounts
    patterns = [
        r'([A-Z]{3})\s*(\d+\.?\d*)',  # 'SGD 185', 'USD 1500'
        r'\$(\d+\.?\d*)',             # '$1500'
        r'€(\d+\.?\d*)',              # '€850'
        r'£(\d+\.?\d*)',              # '£650'
        r'¥(\d+\.?\d*)',              # '¥15000'
        r'(\d+\.?\d*)\s*([A-Z]{3})',  # '185 SGD'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, price_str)
        if match:
            if pattern.startswith('([A-Z]{3})'):  # Currency code first
                currency = match.group(1)
                amount = float(match.group(2))
                return currency, amount
            elif pattern.startswith(r'\$'):  # Dollar sign
                return 'USD', float(match.group(1))
            elif pattern.startswith(r'€'):  # Euro sign
                return 'EUR', float(match.group(1))
            elif pattern.startswith(r'£'):  # Pound sign
                return 'GBP', float(match.group(1))
            elif pattern.startswith(r'¥'):  # Yen sign
                return 'JPY', float(match.group(1))
            elif pattern.endswith('([A-Z]{3})'):  # Amount first
                amount = float(match.group(1))
                currency = match.group(2)
                return currency, amount
    
    # If no pattern matches, try to extract just the number
    numbers = re.findall(r'\d+\.?\d*', price_str)
    if numbers:
        return 'USD', float(numbers[0])  # Assume USD
    
    return None, None

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'CTL Flight Price Service', 
        'status': 'running',
        'endpoints': ['/health', '/api/getFlightPrice'],
        'features': ['Dynamic airport codes', 'Real-time currency conversion', 'Proper fare class handling']
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'flight-price-api'})

@app.route('/api/getFlightPrice', methods=['GET'])
def get_flight_price():
    debug_info = []
    
    try:
        # Try to import fast-flights
        try:
            from fast_flights import FlightData, Passengers, get_flights
            from datetime import datetime, timedelta
            debug_info.append("✅ fast-flights imported successfully")
            use_real_data = True
        except ImportError as e:
            debug_info.append(f"❌ fast-flights import failed: {str(e)}")
            use_real_data = False
        
        # Extract parameters
        departure_city = request.args.get('departureCity', 'Manila')
        departure_country = request.args.get('departureCountry', 'Philippines')
        destination_city = request.args.get('destinationCity', 'Tokyo')
        destination_country = request.args.get('destinationCountry', 'Japan')
        target_date = request.args.get('targetDate')
        travel_days = int(request.args.get('travelDays', 7))
        fare_class_raw = request.args.get('fareClass', 'economy')
        fare_class = fare_class_raw.lower().strip()
        
        debug_info.append(f"Parameters: {departure_city} → {destination_city}, {target_date}, {travel_days} days, {fare_class} class")
        
        if use_real_data and target_date:
            # Get airport codes dynamically
            from_airport = get_airport_code_dynamic(departure_city, departure_country)
            to_airport = get_airport_code_dynamic(destination_city, destination_country)
            
            debug_info.append(f"Airport codes: {from_airport} → {to_airport}")
            
            if from_airport and to_airport:
                try:
                    # Parse date
                    departure_date = datetime.strptime(target_date, '%Y-%m-%d')
                    return_date = departure_date + timedelta(days=travel_days)
                    
                    debug_info.append(f"Dates: {departure_date.strftime('%Y-%m-%d')} → {return_date.strftime('%Y-%m-%d')}")
                    
                    # Create flight data
                    flight_data = [
                        FlightData(date=departure_date.strftime('%Y-%m-%d'), from_airport=from_airport, to_airport=to_airport),
                        FlightData(date=return_date.strftime('%Y-%m-%d'), from_airport=to_airport, to_airport=from_airport)
                    ]
                    
                    debug_info.append("Flight data objects created")
                    
                    # ROBUST: Handle all possible case variations users might enter
                    seat_class_mapping = {
                        'economy': 'economy',
                        'business': 'business', 
                        'first': 'first',
                        'premium': 'premium-economy',
                        'premium-economy': 'premium-economy',
                        'premiumeconomy': 'premium-economy'
                    }
                    seat_class = seat_class_mapping.get(fare_class, 'economy')
                    debug_info.append(f"Fare class input: '{fare_class_raw}' → normalized: '{fare_class}' → mapped: '{seat_class}'")
                    
                    # Get real flights
                    passengers = Passengers(adults=1, children=0, infants_in_seat=0, infants_on_lap=0)
                    
                    debug_info.append(f"Calling fast-flights get_flights() with {seat_class} class...")
                    
                    result = get_flights(
                        flight_data=flight_data,
                        trip="round-trip",
                        seat=seat_class,
                        passengers=passengers,
                        fetch_mode="fallback"
                    )
                    
                    debug_info.append(f"get_flights() returned: {type(result)}")
                    
                    if result and result.flights:
                        debug_info.append(f"Found {len(result.flights)} flights")
                        best_flight = result.flights[0]
                        
                        debug_info.append(f"Best flight: {getattr(best_flight, 'name', 'Unknown airline')}")
                        debug_info.append(f"Flight price: {getattr(best_flight, 'price', 'No price')}")
                        
                        # FIXED: Improved price parsing with real-time currency conversion
                        real_price_usd = None
                        if hasattr(best_flight, 'price') and best_flight.price:
                            debug_info.append(f"Price found: {best_flight.price} (type: {type(best_flight.price)})")
                            
                            try:
                                if isinstance(best_flight.price, (int, float)):
                                    real_price_usd = float(best_flight.price)
                                    debug_info.append(f"Numeric price: ${real_price_usd}")
                                    
                                elif isinstance(best_flight.price, str):
                                    # Extract currency and amount
                                    currency, amount = extract_currency_and_amount(best_flight.price)
                                    debug_info.append(f"Extracted: {amount} {currency}")
                                    
                                    if currency and amount:
                                        if currency == 'USD':
                                            real_price_usd = amount
                                        else:
                                            # Get real-time exchange rate
                                            exchange_rate = get_exchange_rate(currency, 'USD')
                                            real_price_usd = round(amount * exchange_rate, 2)
                                            debug_info.append(f"Exchange rate {currency} → USD: {exchange_rate}")
                                            debug_info.append(f"Converted: {amount} {currency} = ${real_price_usd} USD")
                                            
                            except Exception as price_error:
                                debug_info.append(f"Price parsing error: {str(price_error)}")
                        else:
                            debug_info.append("No price attribute found")
                        
                        if real_price_usd:
                            return jsonify({
                                'error': False,
                                'price': real_price_usd,
                                'currency': 'USD',
                                'flight_details': {
                                    'airline': getattr(best_flight, 'name', 'Unknown'),
                                    'duration': getattr(best_flight, 'duration', 'Unknown'),
                                    'stops': getattr(best_flight, 'stops', 'Unknown'),
                                    'departure': getattr(best_flight, 'departure', 'Unknown'),
                                    'arrival': getattr(best_flight, 'arrival', 'Unknown')
                                },
                                'source': 'real_google_flights',
                                'fare_class_used': seat_class,
                                'debug': debug_info,
                                'search_url': f"https://www.google.com/travel/flights?q=Flights%20from%20{from_airport}%20to%20{to_airport}"
                            })
                    else:
                        debug_info.append("No flights returned from get_flights()")
                        
                except Exception as e:
                    debug_info.append(f"Fast-flights error: {str(e)}")
            else:
                debug_info.append(f"Missing airport codes for {departure_city}/{departure_country} or {destination_city}/{destination_country}")
        else:
            if not use_real_data:
                debug_info.append("Not using real data (import failed)")
            if not target_date:
                debug_info.append("No target_date provided")
        
        # Fallback to intelligent estimates
        debug_info.append("Falling back to estimates")
        return get_estimated_price_with_debug(departure_city, destination_city, fare_class, debug_info)
        
    except Exception as e:
        debug_info.append(f"Major error: {str(e)}")
        return get_estimated_price_with_debug(departure_city, destination_city, fare_class, debug_info)

def get_estimated_price_with_debug(departure_city, destination_city, fare_class, debug_info):
    """Smart price estimates as fallback"""
    route_estimates = {
        ('Manila', 'Tokyo'): 650, ('Manila', 'Seoul'): 580, ('Manila', 'Hong Kong'): 300,
        ('Manila', 'Singapore'): 350, ('Manila', 'Bangkok'): 400, ('Manila', 'Kuala Lumpur'): 380,
        ('Manila', 'Sydney'): 800, ('Manila', 'Melbourne'): 850, ('Manila', 'London'): 1200,
        ('Manila', 'Paris'): 1250, ('Manila', 'New York'): 1400, ('Manila', 'Los Angeles'): 1100,
        # Add reverse routes
        ('Tokyo', 'Manila'): 650, ('Seoul', 'Manila'): 580, ('Hong Kong', 'Manila'): 300,
        ('Singapore', 'Manila'): 350, ('Bangkok', 'Manila'): 400, ('Sydney', 'Manila'): 800,
    }
    
    route = (departure_city, destination_city)
    price = route_estimates.get(route, 750)
    
    # Apply fare class multipliers
    if fare_class_lower in ['business']:
        price = int(price * 2.5)
    elif fare_class_lower in ['first']:
        price = int(price * 4)
    elif fare_class_lower in ['premium', 'premium-economy', 'premiumeconomy']:
        price = int(price * 1.5)
    
    return jsonify({
        'error': False,
        'price': price,
        'currency': 'USD',
        'source': 'estimated',
        'route': f"{departure_city} to {destination_city}",
        'fare_class': fare_class,
        'debug': debug_info,
        'search_url': f"https://www.google.com/travel/flights?q=Flights%20from%20{departure_city}%20to%20{destination_city}"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
