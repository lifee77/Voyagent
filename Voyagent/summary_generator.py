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
    
    # Activities
    if trip_details["activities"]:
        summary += "## 🎭 Recommended Activities\n\n"
        for idx, activity in enumerate(trip_details["activities"][:5], 1):
            summary += f"{idx}. {activity.get('name', 'Unknown activity')}"
            if activity.get('rating'):
                summary += f" ({activity.get('rating')}★)"
            summary += f"\n   - {activity.get('description', 'No description available')[:100]}...\n\n"
    
    # Accommodations
    if trip_details["accommodations"]:
        summary += "## 🏨 Accommodation Options\n\n"
        for idx, accommodation in enumerate(trip_details["accommodations"][:3], 1):
            summary += f"{idx}. {accommodation.get('name', 'Unknown accommodation')}\n"
            if accommodation.get('address'):
                summary += f"   - Address: {accommodation.get('address')}\n"
            if accommodation.get('price'):
                summary += f"   - Price: {accommodation.get('price')}\n"
            summary += "\n"
    
    # Notes
    if trip_details["notes"]:
        summary += "## 📝 Notes\n\n"
        for note in trip_details["notes"]:
            summary += f"- {note}\n"
        summary += "\n"
    
    # Call to action
    summary += "---\n"
    summary += "Need more details? Ask me about specific attractions, restaurants, or travel tips for your destination!"
    
    return summary