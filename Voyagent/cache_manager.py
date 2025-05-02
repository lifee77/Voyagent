import os
import json
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Cache directory
CACHE_DIR = Path(__file__).parent / "cache"

# Ensure cache directory exists
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def get_user_cache_file(user_id):
    """Get the cache file path for a specific user"""
    return CACHE_DIR / f"user_{user_id}.json"

def save_to_cache(user_id, query, result):
    """Save information to the user's cache file"""
    cache_file = get_user_cache_file(user_id)
    
    # Initialize or load existing cache data
    if cache_file.exists():
        with open(cache_file, 'r') as f:
            cache_data = json.load(f)
    else:
        cache_data = {
            "user_id": user_id,
            "last_updated": datetime.now().isoformat(),
            "trip_details": {
                "destinations": [],
                "dates": {},
                "flights": [],
                "accommodations": [],
                "activities": [],
                "reservations": [],
                "notes": []
            },
            "queries": []
        }

    # Extract information from the result
    output_text = result.get("output", "")
    tool_calls = []
    
    # Extract information from tool calls
    for step in result.get("intermediate_steps", []):
        tool_name = step[0].tool
        tool_input = step[0].tool_input
        tool_output = step[1]
        
        tool_calls.append({
            "tool": tool_name,
            "input": tool_input,
            "output": tool_output
        })
        
        # Extract and save specific information based on tool type
        if tool_name == "apify_flight":
            _extract_flight_info(cache_data, tool_output)
        elif tool_name == "apify_poi":
            _extract_poi_info(cache_data, tool_output)
        elif tool_name == "perplexity_search":
            _extract_destination_info(cache_data, query, tool_output)
        elif tool_name == "rime_reservation":
            _extract_reservation_info(cache_data, tool_input, tool_output)
    
    # Add this query to the history
    cache_data["queries"].append({
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "response": output_text,
        "tool_calls": tool_calls
    })
    
    # Update last_updated timestamp
    cache_data["last_updated"] = datetime.now().isoformat()
    
    # Save to file
    with open(cache_file, 'w') as f:
        json.dump(cache_data, f, indent=2)
    
    logger.info(f"Updated cache for user {user_id}")

def get_from_cache(user_id):
    """Get the cached information for a user"""
    cache_file = get_user_cache_file(user_id)
    
    if cache_file.exists():
        with open(cache_file, 'r') as f:
            return json.load(f)
    
    return None

def _extract_flight_info(cache_data, tool_output):
    """Extract flight information from tool output"""
    try:
        # Parse the tool output as JSON if it's a string
        if isinstance(tool_output, str):
            flights_data = json.loads(tool_output)
        else:
            flights_data = tool_output
        
        # Check if we have a list of flights
        if isinstance(flights_data, list):
            for flight in flights_data[:3]:  # Take top 3 flights
                if isinstance(flight, dict):
                    flight_info = {
                        "from": flight.get("departureAirport", ""),
                        "to": flight.get("arrivalAirport", ""),
                        "departure_date": flight.get("departureDate", ""),
                        "arrival_date": flight.get("arrivalDate", ""),
                        "airline": flight.get("airline", ""),
                        "price": flight.get("price", ""),
                        "duration": flight.get("duration", "")
                    }
                    
                    # Add to destinations if not already there
                    origin = flight.get("departureCity", "")
                    destination = flight.get("arrivalCity", "")
                    
                    if origin and origin not in cache_data["trip_details"]["destinations"]:
                        cache_data["trip_details"]["destinations"].append(origin)
                    
                    if destination and destination not in cache_data["trip_details"]["destinations"]:
                        cache_data["trip_details"]["destinations"].append(destination)
                    
                    # Add to flights if not duplicate
                    if flight_info not in cache_data["trip_details"]["flights"]:
                        cache_data["trip_details"]["flights"].append(flight_info)
        
    except Exception as e:
        logger.error(f"Error extracting flight info: {e}")

def _extract_poi_info(cache_data, tool_output):
    """Extract points of interest information from tool output"""
    try:
        # Parse the tool output as JSON if it's a string
        if isinstance(tool_output, str):
            poi_data = json.loads(tool_output)
        else:
            poi_data = tool_output
        
        # Check if we have a list of POIs
        if isinstance(poi_data, list):
            for poi in poi_data[:5]:  # Take top 5 POIs
                if isinstance(poi, dict):
                    poi_info = {
                        "name": poi.get("name", ""),
                        "type": poi.get("type", "attraction"),
                        "location": poi.get("location", ""),
                        "rating": poi.get("rating", ""),
                        "description": poi.get("description", "")
                    }
                    
                    # Add to activities if not duplicate
                    if poi_info not in cache_data["trip_details"]["activities"]:
                        cache_data["trip_details"]["activities"].append(poi_info)
                    
                    # Add location to destinations if not already there
                    location = poi.get("location", "")
                    if location and location not in cache_data["trip_details"]["destinations"]:
                        cache_data["trip_details"]["destinations"].append(location)
        
    except Exception as e:
        logger.error(f"Error extracting POI info: {e}")

def _extract_destination_info(cache_data, query, tool_output):
    """Extract destination information from search query and results"""
    try:
        # Find destination mentions in the query
        common_destination_keywords = ["in", "to", "visit", "traveling to", "flight to"]
        
        for keyword in common_destination_keywords:
            if keyword in query.lower():
                parts = query.lower().split(keyword)
                if len(parts) > 1:
                    potential_destination = parts[1].strip().split()[0].capitalize()
                    if len(potential_destination) > 3:  # Avoid short words
                        if potential_destination not in cache_data["trip_details"]["destinations"]:
                            cache_data["trip_details"]["destinations"].append(potential_destination)
        
        # Extract potential dates
        date_keywords = ["on", "from", "between", "during"]
        months = ["january", "february", "march", "april", "may", "june", "july", 
                 "august", "september", "october", "november", "december",
                 "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        
        query_lower = query.lower()
        for month in months:
            if month in query_lower:
                # If month is mentioned, add as potential travel date
                if "travel_dates" not in cache_data["trip_details"]["dates"]:
                    cache_data["trip_details"]["dates"]["travel_dates"] = month.capitalize()
                
    except Exception as e:
        logger.error(f"Error extracting destination info: {e}")

def _extract_reservation_info(cache_data, tool_input, tool_output):
    """Extract reservation information from Rime tool calls"""
    try:
        # Parse the tool input as JSON to get reservation details
        if isinstance(tool_input, str):
            try:
                reservation_data = json.loads(tool_input)
            except json.JSONDecodeError:
                logger.error("Invalid JSON in Rime tool input")
                return
        else:
            reservation_data = tool_input
        
        # Extract basic information from the reservation
        service_type = reservation_data.get("service_type", "")
        service_name = reservation_data.get("service_name", "")
        user_name = reservation_data.get("user_name", "")
        reservation_details = reservation_data.get("reservation_details", {})
        
        # Create a structured reservation entry
        reservation_info = {
            "service_type": service_type,
            "service_name": service_name,
            "status": "confirmed",  # Assume success for now
            "date": reservation_details.get("date", ""),
            "time": reservation_details.get("time", ""),
            "num_people": reservation_details.get("num_people", ""),
            "details": reservation_details.get("special_requests", ""),
            "confirmation": f"Made via Rime on {datetime.now().strftime('%Y-%m-%d')}"
        }
        
        # Extract confirmation number from the tool output
        if isinstance(tool_output, str):
            confirmation_lines = tool_output.split("\n")
            for line in confirmation_lines:
                if "confirmation" in line.lower() or "reference" in line.lower():
                    reservation_info["confirmation"] = line.strip()
                    break
        
        # Add the reservation if it's not a duplicate
        if reservation_info not in cache_data["trip_details"]["reservations"]:
            cache_data["trip_details"]["reservations"].append(reservation_info)
        
        # If this was a hotel reservation, also add to accommodations
        if service_type.lower() == "hotel":
            accommodation_info = {
                "name": service_name,
                "location": reservation_details.get("location", ""),
                "check_in": reservation_details.get("date", ""),
                "duration": reservation_details.get("duration", ""),
                "price": reservation_details.get("price", ""),
                "confirmation": reservation_info.get("confirmation", "")
            }
            
            if accommodation_info not in cache_data["trip_details"]["accommodations"]:
                cache_data["trip_details"]["accommodations"].append(accommodation_info)
        
    except Exception as e:
        logger.error(f"Error extracting reservation info: {e}")

def clear_cache(user_id=None):
    """Clear cache for a user or all users"""
    if user_id:
        cache_file = get_user_cache_file(user_id)
        if cache_file.exists():
            os.remove(cache_file)
            logger.info(f"Cleared cache for user {user_id}")
    else:
        for cache_file in CACHE_DIR.glob("user_*.json"):
            os.remove(cache_file)
        logger.info("Cleared all user caches")