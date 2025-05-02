import logging
from Voyagent.cache_manager import get_from_cache

# Configure logging
logger = logging.getLogger(__name__)

def generate_summary(user_id):
    """Generate a trip summary from cached information"""
    # Get user data from cache
    cache_data = get_from_cache(user_id)
    
    if not cache_data or "trip_details" not in cache_data:
        return "I don't have enough information to create a summary for your trip. Please ask me about your destinations, flights, or activities first."
    
    trip_details = cache_data["trip_details"]
    
    # Check if we have enough information
    if not trip_details["destinations"]:
        return "I don't have any destination information for your trip yet. Please tell me where you'd like to go."
    
    # Build the summary
    summary = "# 🌍 Your Trip Summary\n\n"
    
    # Destinations
    destinations = ", ".join(trip_details["destinations"])
    summary += f"## 📍 Destinations\n{destinations}\n\n"
    
    # Travel dates
    if trip_details["dates"]:
        dates_info = ", ".join([f"{k}: {v}" for k, v in trip_details["dates"].items()])
        summary += f"## 📅 Travel Dates\n{dates_info}\n\n"
    
    # Flights
    if trip_details["flights"]:
        summary += "## ✈️ Flight Options\n\n"
        for idx, flight in enumerate(trip_details["flights"][:3], 1):
            summary += f"{idx}. {flight.get('airline', 'Unknown airline')}: {flight.get('from', '')} → {flight.get('to', '')}\n"
            summary += f"   - Departure: {flight.get('departure_date', 'Unknown date')}\n"
            summary += f"   - Duration: {flight.get('duration', 'Unknown duration')}\n"
            summary += f"   - Price: {flight.get('price', 'Unknown price')}\n\n"
    
   