import os
import json
import logging
import requests
import time
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dotenv import load_dotenv
from langchain.tools import BaseTool

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

APIFY_BASE_URL = "https://api.apify.com/v2"

class ApifyFlightTool(BaseTool):
    name = "apify_flight"
    description = """
    Uses Apify Skyscanner Flight Finder to search for flight information between cities.
    Can handle natural language queries about travel plans.
    
    Examples:
    - "I want to fly from San Francisco to New York on June 15th"
    - "What are my options for traveling from Miami to Orlando next week?"
    - "Find flights between Chicago and Dallas for December 1st"
    """
    
    def _run(self, query: str) -> str:
        """Run Apify Flight Finder with the given parameters."""
        logger.info(f"TOOL: apify_flight - Query: {query}")
        
        api_token = os.getenv("APIFY_API_TOKEN")
        if not api_token:
            logger.error("Apify API token not found")
            return "Error: Apify API token not configured"
        
        # Parse query to extract parameters
        params = self._parse_flight_query(query)
        
        # If parsing failed to extract locations, try to use fallback
        if not params.get("from") or not params.get("to"):
            # Check if this is a travel query but not necessarily about flights
            if self._is_general_travel_query(query):
                logger.info("Identified as general travel query, switching to location-based search")
                location = self._extract_destination(query)
                if location:
                    return self._handle_destination_query(location, query)
            else:
                logger.warning("Could not parse flight parameters from query")
                return "I couldn't determine the departure and destination cities from your query. Could you please specify where you're traveling from and to?"
        
        # Use the correct Skyscanner flight actor
        actor_id = "jupri~skyscanner-flight"
        
        url = f"{APIFY_BASE_URL}/acts/{actor_id}/runs"
        
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        # Format date properly if available
        departure_date = params.get("date", "")
        if departure_date:
            # Try to ensure date is in YYYY-MM-DD format
            try:
                parsed_date = datetime.strptime(departure_date, "%Y-%m-%d")
                departure_date = parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                # If date parsing fails, try to extract a date range
                departure_date = ""
        
        # Prepare payload based on the Skyscanner actor's expected input schema
        payload = {
            "originLocationCode": params.get("from", ""),
            "destinationLocationCode": params.get("to", ""),
            "departureDate": departure_date,
            "returnDate": "",  # Assuming one-way for simplicity
            "adults": 1,
            "currency": "USD",
            "maxResults": 10,
            "directFlight": False
        }
        
        try:
            logger.info(f"Running Apify actor {actor_id} with payload: {json.dumps(payload)}")
            # Start the actor run
            response = requests.post(url, headers=headers, json=payload, params={"token": api_token})
            response.raise_for_status()
            run_info = response.json()
            run_id = run_info["data"]["id"]
            dataset_id = run_info["data"]["defaultDatasetId"]
            logger.info(f"Apify actor run started: run_id={run_id}, dataset_id={dataset_id}")
            
            # Poll for run completion
            status_url = f"{APIFY_BASE_URL}/actor-runs/{run_id}"
            max_wait_time = 120 # Wait up to 2 minutes
            start_time = time.time()
            while time.time() - start_time < max_wait_time:
                status_resp = requests.get(status_url, params={"token": api_token})
                status_data = status_resp.json()
                run_status = status_data["data"]["status"]
                logger.info(f"Polling Apify run {run_id}: status={run_status}")
                if run_status in ["SUCCEEDED", "FAILED", "TIMED-OUT", "ABORTED"]:
                    break
                time.sleep(5)
            
            if run_status != "SUCCEEDED":
                logger.error(f"Apify actor run {run_id} did not succeed. Status: {run_status}")
                return f"Error: Flight search failed with status {run_status}"

            # Get dataset items
            dataset_url = f"{APIFY_BASE_URL}/datasets/{dataset_id}/items"
            dataset_resp = requests.get(dataset_url, params={"token": api_token, "format": "json", "limit": 10})
            dataset_resp.raise_for_status()
            flights = dataset_resp.json()
            
            if not flights:
                return "No flight results found for this query. There may not be direct flights between these locations."
                 
            logger.info(f"Received {len(flights)} flight results from Apify.")
            return json.dumps(flights)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Apify API: {e}")
            # Check if it's a 404 error specifically for the actor not found
            if hasattr(e, 'response') and e.response.status_code == 404 and 'Not Found' in str(e):
                return "The flight search service is currently unavailable. I'll try to find travel information another way."
            return f"Error searching for flights: {str(e)}"
        except Exception as e:
            logger.error(f"An unexpected error occurred during flight search: {e}", exc_info=True)
            return f"An unexpected error occurred while searching for flights."
    
    def _parse_flight_query(self, query: str) -> dict:
        """Parse the flight query to extract parameters with improved NLP understanding."""
        params = {"from": "", "to": "", "date": ""}
        query_lower = query.lower()
        
        # Extract cities using common travel patterns
        # Pattern 1: "from X to Y"
        from_to_match = re.search(r'from\s+([a-z\s]+)\s+to\s+([a-z\s]+)', query_lower)
        if from_to_match:
            params["from"] = from_to_match.group(1).strip()
            params["to"] = from_to_match.group(2).strip().split(" on ")[0].split(" in ")[0].split(" next ")[0].strip()
        
        # Pattern 2: "X to Y" or "traveling to Y from X"
        elif "to" in query_lower:
            # Try "traveling to Y from X" pattern
            to_from_match = re.search(r'to\s+([a-z\s]+)\s+from\s+([a-z\s]+)', query_lower)
            if to_from_match:
                params["to"] = to_from_match.group(1).strip()
                params["from"] = to_from_match.group(2).strip()
            else:
                # Try "X to Y" pattern
                parts = query_lower.split(" to ")
                if len(parts) > 1:
                    # Take the words before "to" as origin
                    origin_part = parts[0].split()[-3:]  # Last few words before "to"
                    params["from"] = " ".join(origin_part).strip()
                    # Take words after "to" as destination
                    dest_part = parts[1].split()[:3]  # First few words after "to"
                    params["to"] = " ".join(dest_part).strip()
        
        # Pattern 3: "travel/visit/going to Y"
        travel_verbs = ["travel", "visit", "going", "fly", "traveling", "visiting"]
        for verb in travel_verbs:
            if f"{verb} to" in query_lower:
                dest_part = query_lower.split(f"{verb} to")[1].strip().split()[0:3]
                params["to"] = " ".join(dest_part).strip().split(".")[0].strip()
                # For these patterns, try to find origin if mentioned
                if "from" in query_lower:
                    from_part = query_lower.split("from")[1].strip().split()[0:3]
                    params["from"] = " ".join(from_part).strip()
        
        # Extract dates
        # Check for specific date formats
        date_patterns = [
            r'(?:on|for|date[:\s])\s*(\d{4}-\d{1,2}-\d{1,2})',  # YYYY-MM-DD
            r'(?:on|for|date[:\s])\s*(\d{1,2}/\d{1,2}/\d{4})',  # MM/DD/YYYY
            r'(?:on|for|date[:\s])\s*(\d{1,2}/\d{1,2}/\d{2})',  # MM/DD/YY
            r'(?:on|for|date[:\s])\s*([a-z]+\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s*\d{4})?)'  # Month DD, YYYY
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, query_lower)
            if date_match:
                date_str = date_match.group(1).strip()
                params["date"] = self._normalize_date(date_str)
                break
        
        # Check for relative dates
        relative_date_patterns = [
            (r'next\s+(week|month)', lambda m: self._calculate_relative_date(m.group(1))),
            (r'in\s+(\d+)\s+(day|week|month)s?', lambda m: self._calculate_relative_date(m.group(2), int(m.group(1))))
        ]
        
        for pattern, date_func in relative_date_patterns:
            rel_date_match = re.search(pattern, query_lower)
            if rel_date_match:
                params["date"] = date_func(rel_date_match)
                break
        
        # Extract destinations from more complex queries with landmarks or attractions
        if not params["to"] and "yosemite" in query_lower:
            params["to"] = "Yosemite National Park"
            if not params["from"] and ("san francisco" in query_lower or "sf" in query_lower):
                params["from"] = "San Francisco"
            
            # Try to extract date from queries like "2nd week of May"
            week_match = re.search(r'(\d+)(?:st|nd|rd|th)?\s+week\s+of\s+([a-z]+)', query_lower)
            if week_match:
                week_num = int(week_match.group(1))
                month = week_match.group(2)
                params["date"] = self._calculate_week_of_month(week_num, month)
                
        return params
    
    def _normalize_date(self, date_str: str) -> str:
        """Convert various date formats to YYYY-MM-DD."""
        try:
            # Try various formats
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%B %d, %Y", "%B %d %Y", "%b %d, %Y", "%b %d %Y"]:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
                    
            # Handle "Month Day" without year
            for fmt in ["%B %d", "%b %d"]:
                try:
                    # Assume current year
                    dt = datetime.strptime(f"{date_str}, {datetime.now().year}", f"{fmt}, %Y")
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
                    
        except Exception:
            pass
            
        return date_str  # Return as-is if parsing fails
    
    def _calculate_relative_date(self, unit: str, amount: int = 1) -> str:
        """Calculate relative dates like 'next week' or 'in 3 days'."""
        today = datetime.now()
        
        if unit.lower() == 'day':
            future = today + timedelta(days=amount)
        elif unit.lower() == 'week':
            future = today + timedelta(weeks=amount)
        elif unit.lower() == 'month':
            # Approximate a month as 30 days
            future = today + timedelta(days=30*amount)
        else:
            return ""
            
        return future.strftime("%Y-%m-%d")
    
    def _calculate_week_of_month(self, week_num: int, month_name: str) -> str:
        """Calculate a date from expressions like '2nd week of May'."""
        try:
            now = datetime.now()
            year = now.year
            
            # Convert month name to number
            month_num = {
                'january': 1, 'february': 2, 'march': 3, 'april': 4,
                'may': 5, 'june': 6, 'july': 7, 'august': 8,
                'september': 9, 'october': 10, 'november': 11, 'december': 12,
                'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
            }.get(month_name.lower())
            
            if not month_num:
                return ""
                
            # If the month is in the past for this year, assume next year
            if month_num < now.month:
                year += 1
                
            # Calculate the date for the first day of the month
            first_day = datetime(year, month_num, 1)
            
            # Calculate the date for the beginning of the requested week
            # Weeks start on Sunday, so the 2nd week starts on the 8th, etc.
            day_of_month = 1 + (week_num - 1) * 7
            target_date = datetime(year, month_num, min(day_of_month, 28))  # Cap at 28 to avoid month overflow
            
            return target_date.strftime("%Y-%m-%d")
        except Exception:
            return ""
    
    def _is_general_travel_query(self, query: str) -> bool:
        """Determine if this is a general travel query that might not be specifically about flights."""
        query_lower = query.lower()
        travel_terms = ["travel", "visit", "trip", "vacation", "tour", "journey", "exploring"]
        question_terms = ["what should i do", "what are my options", "how can i get", "how to get"]
        
        # Check if it contains travel terms and question patterns
        has_travel_terms = any(term in query_lower for term in travel_terms)
        has_question = any(term in query_lower for term in question_terms)
        
        # Check for destination without specific flight request
        destination_mentioned = any(f"to {place}" in query_lower for place in ["yosemite", "national park", "beach", "mountain"])
        
        return (has_travel_terms or has_question) and destination_mentioned
    
    def _extract_destination(self, query: str) -> str:
        """Extract the main destination from a general travel query."""
        query_lower = query.lower()
        
        # Check for specific destinations
        common_destinations = ["yosemite", "grand canyon", "new york", "las vegas", "paris", "tokyo"]
        for dest in common_destinations:
            if dest in query_lower:
                return dest.title()
        
        # Try to extract destination using "to" patterns
        to_patterns = [r'to\s+([a-z\s]+)(?:\s|\.|\?|$)', r'visit(?:ing)?\s+([a-z\s]+)(?:\s|\.|\?|$)']
        for pattern in to_patterns:
            match = re.search(pattern, query_lower)
            if match:
                destination = match.group(1).strip()
                # Remove trailing words that aren't part of the destination
                words_to_remove = ["for", "in", "on", "during", "next", "this", "from"]
                for word in words_to_remove:
                    if destination.endswith(f" {word}"):
                        destination = destination.rsplit(" ", 1)[0]
                return destination.title()
        
        return ""
    
    def _handle_destination_query(self, location: str, original_query: str) -> str:
        """Handle a query about a destination rather than a specific flight search."""
        logger.info(f"Redirecting flight query to location-based search for: {location}")
        
        # Create a message suggesting using a different tool
        msg = {
            "result": "redirect_to_location",
            "location": location,
            "original_query": original_query,
            "suggested_tools": ["apify_poi", "apify_google_maps"],
            "message": f"I found that you're interested in traveling to {location}. To get information about attractions, activities, and transportation options at this destination, I recommend using a location-based search instead."
        }
        
        return json.dumps(msg)

class ApifyPOITool(BaseTool):
    name = "apify_poi"
    description = """
    Uses Apify Tripadvisor Scraper actor to find points of interest, attractions, restaurants, 
    and activities in a destination city.
    
    Input should be a city or location name, e.g., "Paris, France" or "Tokyo"
    """
    
    def _run(self, location: str) -> str:
        """Run Apify Tripadvisor Scraper with the given location."""
        logger.info(f"TOOL: apify_poi - Location: {location}")
        
        # Check if the input looks like a query rather than a location
        if len(location.split()) > 4 or "?" in location:
            logger.warning(f"Input looks like a query rather than a location: {location}")
            return f"Error: Cannot process this as a location. Please provide a specific destination name."
        
        api_token = os.getenv("APIFY_API_TOKEN")
        if not api_token:
            logger.error("Apify API token not found")
            return "Error: Apify API token not configured"
        
        # Use the correct Tripadvisor scraper actor ID
        actor_id = "maxcopell~tripadvisor"  # Updated to the correct actor ID
        url = f"{APIFY_BASE_URL}/acts/{actor_id}/runs"
        
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        # Prepare payload based on actor's expected input schema
        payload = {
            "locationFullName": location,
            "includeRestaurants": True,
            "includeAttractions": True,
            "includeHotels": False, # Exclude hotels for now
            "maxItems": 10
        }
        
        try:
            logger.info(f"Running Apify actor {actor_id} with payload: {json.dumps(payload)}")
            # Start the actor run
            response = requests.post(url, headers=headers, json=payload, params={"token": api_token})
            response.raise_for_status()
            run_info = response.json()
            run_id = run_info["data"]["id"]
            dataset_id = run_info["data"]["defaultDatasetId"]
            logger.info(f"Apify actor run started: run_id={run_id}, dataset_id={dataset_id}")

            # Poll for run completion with timeout
            status_url = f"{APIFY_BASE_URL}/actor-runs/{run_id}"
            max_wait_time = 60  # Reduced timeout to 60 seconds (1 minute)
            start_time = time.time()
            while time.time() - start_time < max_wait_time:
                status_resp = requests.get(status_url, params={"token": api_token})
                status_data = status_resp.json()
                run_status = status_data["data"]["status"]
                logger.info(f"Polling Apify run {run_id}: status={run_status}")
                if run_status in ["SUCCEEDED", "FAILED", "TIMED-OUT", "ABORTED"]:
                    break
                time.sleep(5)
            
            # Check if we timed out
            elapsed_time = time.time() - start_time
            if elapsed_time >= max_wait_time:
                logger.warning(f"Apify actor run timed out after {elapsed_time:.1f} seconds")
                return f"Error: POI search timed out after {elapsed_time:.1f} seconds. Consider using a more specific location name or trying a different search."
                
            if run_status != "SUCCEEDED":
                logger.error(f"Apify actor run {run_id} did not succeed. Status: {run_status}")
                return f"Error: POI search failed with status {run_status}"

            # Get dataset items
            dataset_url = f"{APIFY_BASE_URL}/datasets/{dataset_id}/items"
            dataset_resp = requests.get(dataset_url, params={"token": api_token, "format": "json", "limit": 10})
            dataset_resp.raise_for_status()
            pois = dataset_resp.json()
            
            if not pois:
                 return "No points of interest found for this location."
                 
            logger.info(f"Received {len(pois)} POI results from Apify.")
            return json.dumps(pois)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Apify API: {e}")
            return f"Error searching for points of interest: {str(e)}"
        except Exception as e:
            logger.error(f"An unexpected error occurred during POI search: {e}", exc_info=True)
            return f"An unexpected error occurred while searching for points of interest."

class ApifyGoogleMapsTool(BaseTool):
    name = "apify_google_maps"
    description = """
    Uses Apify Google Maps Scraper actor to find specific places like restaurants, get driving directions/times, 
    or find general information about locations from Google Maps.
    
    Input should be a specific query for Google Maps, such as:
    - "restaurants near Yosemite Valley Lodge"
    - "driving directions from San Francisco Airport to Yosemite Valley"
    - "details about The Ahwahnee hotel"
    - "photos of Vernal Fall Yosemite"
    """
    
    def _run(self, query: str) -> str:
        """Run Apify Google Maps Scraper with the given query."""
        logger.info(f"TOOL: apify_google_maps - Query: {query}")
        
        api_token = os.getenv("APIFY_API_TOKEN")
        if not api_token:
            logger.error("Apify API token not found")
            return "Error: Apify API token not configured"
        
        # Use the specified Google Maps scraper actor ID
        actor_id = "nwua9Gu5YrADL7ZDj" # Updated to correct actor ID from the provided URL
        url = f"{APIFY_BASE_URL}/acts/{actor_id}/runs"
        
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        # Prepare payload based on the specific actor's expected input schema
        payload = {
            "searchStrings": [query],
            "maxCrawledPlaces": 5,
            "language": "en",
            "saveReviews": False,
            "saveImages": True,
            "savePopularTimes": True,
            "maxReviews": 0,
            "maxImages": 3,
            "exportPlaceUrls": False
        }
        
        # Check if it looks like a directions query
        if "directions" in query.lower() or "driving time" in query.lower() or "how to get" in query.lower():
            # Extract origin and destination if possible
            origin_dest = self._extract_directions_endpoints(query)
            if origin_dest:
                payload["directionsStartPoint"] = origin_dest[0]
                payload["directionsEndPoint"] = origin_dest[1]
                payload["directionsMode"] = "driving" # Default to driving mode
                logger.info(f"Detected directions query: {origin_dest[0]} → {origin_dest[1]}")
        
        try:
            logger.info(f"Running Apify actor {actor_id} with payload: {json.dumps(payload)}")
            # Start the actor run
            response = requests.post(url, headers=headers, json=payload, params={"token": api_token})
            response.raise_for_status()
            run_info = response.json()
            run_id = run_info["data"]["id"]
            dataset_id = run_info["data"]["defaultDatasetId"]
            logger.info(f"Apify actor run started: run_id={run_id}, dataset_id={dataset_id}")

            # Poll for run completion
            status_url = f"{APIFY_BASE_URL}/actor-runs/{run_id}"
            max_wait_time = 180 # Wait up to 3 minutes
            start_time = time.time()
            while time.time() - start_time < max_wait_time:
                status_resp = requests.get(status_url, params={"token": api_token})
                status_data = status_resp.json()
                run_status = status_data["data"]["status"]
                logger.info(f"Polling Apify run {run_id}: status={run_status}")
                if run_status in ["SUCCEEDED", "FAILED", "TIMED-OUT", "ABORTED"]:
                    break
                time.sleep(5)
                
            if run_status != "SUCCEEDED":
                logger.error(f"Apify actor run {run_id} did not succeed. Status: {run_status}")
                return f"Error: Google Maps search failed with status {run_status}"

            # Get dataset items
            dataset_url = f"{APIFY_BASE_URL}/datasets/{dataset_id}/items"
            # Fetch appropriate number of results
            limit = 10  # Default limit
            dataset_resp = requests.get(dataset_url, params={"token": api_token, "format": "json", "limit": limit})
            dataset_resp.raise_for_status()
            maps_data = dataset_resp.json()
            
            if not maps_data:
                 return "No results found on Google Maps for this query."
                 
            logger.info(f"Received {len(maps_data)} results from Apify Google Maps Scraper.")
            return json.dumps(maps_data)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Apify API: {e}")
            return f"Error searching Google Maps: {str(e)}"
        except Exception as e:
            logger.error(f"An unexpected error occurred during Google Maps search: {e}", exc_info=True)
            return f"An unexpected error occurred while searching Google Maps."
    
    def _extract_directions_endpoints(self, query: str) -> Optional[Tuple[str, str]]:
        """Extract origin and destination from a directions query."""
        query_lower = query.lower()
        
        # Try various patterns for directions
        patterns = [
            r'directions\s+from\s+([^\.]+)\s+to\s+([^\.]+)', 
            r'how\s+to\s+get\s+from\s+([^\.]+)\s+to\s+([^\.]+)',
            r'route\s+from\s+([^\.]+)\s+to\s+([^\.]+)',
            r'([^\.]+)\s+to\s+([^\.]+)\s+directions'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                origin = match.group(1).strip()
                destination = match.group(2).strip()
                return origin, destination
        
        return None