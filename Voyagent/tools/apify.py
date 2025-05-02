import os
import json
import logging
import requests
import time
from dotenv import load_dotenv
from langchain.tools import BaseTool

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class ApifyFlightTool(BaseTool):
    name = "apify_flight"
    description = """
    Uses Apify Flight Finder actor to search for flight information between cities.
    Provide the departure city, destination city, and optional date in the input.
    
    Input should be in the format: "from: [departure city], to: [destination city], date: [YYYY-MM-DD]"
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
        
        # In a real implementation, call the Apify Flight Finder actor
        # actor_id = "arindam_1729/flight-finder"
        # url = f"https://api.apify.com/v2/acts/{actor_id}/runs"
        
        # headers = {
        #     "Authorization": f"Bearer {api_token}",
        #     "Content-Type": "application/json"
        # }
        
        # payload = {
        #     "fromLocation": params["from"],
        #     "toLocation": params["to"],
        #     "date": params.get("date", ""),
        #     "directFlights": True,
        #     "currency": "USD"
        # }
        
        try:
            # Uncomment for actual API call
            # response = requests.post(url, headers=headers, json=payload)
            # response.raise_for_status()
            # run_info = response.json()
            # run_id = run_info["data"]["id"]
            
            # # Poll for run completion
            # status_url = f"https://api.apify.com/v2/actor-runs/{run_id}"
            # while True:
            #     status_resp = requests.get(status_url, headers=headers)
            #     status_data = status_resp.json()
            #     if status_data["data"]["status"] in ["SUCCEEDED", "FAILED", "TIMED-OUT"]:
            #         break
            #     time.sleep(2)
            
            # # Get dataset items
            # dataset_id = status_data["data"]["defaultDatasetId"]
            # dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
            # dataset_resp = requests.get(dataset_url, headers=headers)
            # flights = dataset_resp.json()
            # return flights
            
            # For demo purposes, return mock data
            mock_flights = self._get_mock_flights(params)
            return json.dumps(mock_flights)
            
        except Exception as e:
            logger.error(f"Error calling Apify API: {e}")
            return f"Error searching for flights: {str(e)}"
    
    def _parse_flight_query(self, query: str) -> dict:
        """Parse the flight query to extract parameters."""
        params = {"from": "", "to": "", "date": ""}
        
        for part in query.split(","):
            part = part.strip().lower()
            
            if part.startswith("from:"):
                params["from"] = part[5:].strip()
            elif part.startswith("to:"):
                params["to"] = part[3:].strip()
            elif part.startswith("date:"):
                params["date"] = part[5:].strip()
        
        return params
    
    def _get_mock_flights(self, params: dict) -> list:
        """Generate mock flight data for demo purposes."""
        from_city = params["from"].lower()
        to_city = params["to"].lower()
        
        if "new york" in from_city and "london" in to_city:
            return [
                {
                    "airline": "British Airways",
                    "flightNumber": "BA178",
                    "departureAirport": "JFK",
                    "arrivalAirport": "LHR",
                    "departureCity": "New York",
                    "arrivalCity": "London",
                    "departureDate": "2025-05-15T19:30:00",
                    "arrivalDate": "2025-05-16T07:45:00",
                    "duration": "7h 15m",
                    "price": "$742",
                    "currency": "USD",
                    "stopCount": 0,
                    "cabinClass": "Economy"
                },
                {
                    "airline": "United Airlines",
                    "flightNumber": "UA14",
                    "departureAirport": "EWR",
                    "arrivalAirport": "LHR",
                    "departureCity": "New York",
                    "arrivalCity": "London",
                    "departureDate": "2025-05-15T18:15:00",
                    "arrivalDate": "2025-05-16T06:30:00",
                    "duration": "7h 15m",
                    "price": "$689",
                    "currency": "USD",
                    "stopCount": 0,
                    "cabinClass": "Economy"
                },
                {
                    "airline": "Virgin Atlantic",
                    "flightNumber": "VS4",
                    "departureAirport": "JFK",
                    "arrivalAirport": "LHR",
                    "departureCity": "New York",
                    "arrivalCity": "London",
                    "departureDate": "2025-05-15T21:00:00",
                    "arrivalDate": "2025-05-16T09:20:00",
                    "duration": "7h 20m",
                    "price": "$715",
                    "currency": "USD",
                    "stopCount": 0,
                    "cabinClass": "Economy"
                }
            ]
        elif "tokyo" in from_city and "paris" in to_city:
            return [
                {
                    "airline": "Air France",
                    "flightNumber": "AF275",
                    "departureAirport": "NRT",
                    "arrivalAirport": "CDG",
                    "departureCity": "Tokyo",
                    "arrivalCity": "Paris",
                    "departureDate": "2025-05-20T11:45:00",
                    "arrivalDate": "2025-05-20T17:25:00",
                    "duration": "12h 40m",
                    "price": "$1,230",
                    "currency": "USD",
                    "stopCount": 0,
                    "cabinClass": "Economy"
                },
                {
                    "airline": "Japan Airlines",
                    "flightNumber": "JL215",
                    "departureAirport": "HND",
                    "arrivalAirport": "CDG",
                    "departureCity": "Tokyo",
                    "arrivalCity": "Paris",
                    "departureDate": "2025-05-20T10:30:00",
                    "arrivalDate": "2025-05-20T16:15:00",
                    "duration": "12h 45m",
                    "price": "$1,315",
                    "currency": "USD",
                    "stopCount": 0,
                    "cabinClass": "Economy"
                }
            ]
        elif "berlin" in from_city and "rome" in to_city:
            return [
                {
                    "airline": "Lufthansa",
                    "flightNumber": "LH230",
                    "departureAirport": "TXL",
                    "arrivalAirport": "FCO",
                    "departureCity": "Berlin",
                    "arrivalCity": "Rome",
                    "departureDate": "2025-05-18T14:25:00",
                    "arrivalDate": "2025-05-18T16:40:00",
                    "duration": "2h 15m",
                    "price": "€187",
                    "currency": "EUR",
                    "stopCount": 0,
                    "cabinClass": "Economy"
                },
                {
                    "airline": "Ryanair",
                    "flightNumber": "FR8542",
                    "departureAirport": "SXF",
                    "arrivalAirport": "CIA",
                    "departureCity": "Berlin",
                    "arrivalCity": "Rome",
                    "departureDate": "2025-05-18T10:05:00",
                    "arrivalDate": "2025-05-18T12:15:00",
                    "duration": "2h 10m",
                    "price": "€93",
                    "currency": "EUR",
                    "stopCount": 0,
                    "cabinClass": "Economy"
                }
            ]
        else:
            return [
                {
                    "airline": "Generic Airline",
                    "flightNumber": "GA123",
                    "departureAirport": "AAA",
                    "arrivalAirport": "BBB",
                    "departureCity": params["from"].capitalize(),
                    "arrivalCity": params["to"].capitalize(),
                    "departureDate": "2025-05-15T10:00:00",
                    "arrivalDate": "2025-05-15T14:00:00",
                    "duration": "4h 00m",
                    "price": "$500",
                    "currency": "USD",
                    "stopCount": 0,
                    "cabinClass": "Economy"
                }
            ]


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
        
        api_token = os.getenv("APIFY_API_TOKEN")
        if not api_token:
            logger.error("Apify API token not found")
            return "Error: Apify API token not configured"
        
        # In a real implementation, call the Apify Tripadvisor Scraper actor
        # actor_id = "maxcopell/tripadvisor"
        # url = f"https://api.apify.com/v2/acts/{actor_id}/runs"
        
        # headers = {
        #     "Authorization": f"Bearer {api_token}",
        #     "Content-Type": "application/json"
        # }
        
        # payload = {
        #     "locationFullName": location,
        #     "includeAttractions": True,
        #     "includeRestaurants": True,
        #     "includeHotels": False,
        #     "maxItems": 10
        # }
        
        try:
            # Uncomment for actual API call
            # response = requests.post(url, headers=headers, json=payload)
            # response.raise_for_status()
            # run_info = response.json()
            # run_id = run_info["data"]["id"]
            
            # # Poll for run completion
            # status_url = f"https://api.apify.com/v2/actor-runs/{run_id}"
            # while True:
            #     status_resp = requests.get(status_url, headers=headers)
            #     status_data = status_resp.json()
            #     if status_data["data"]["status"] in ["SUCCEEDED", "FAILED", "TIMED-OUT"]:
            #         break
            #     time.sleep(2)
            
            # # Get dataset items
            # dataset_id = status_data["data"]["defaultDatasetId"]
            # dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
            # dataset_resp = requests.get(dataset_url, headers=headers)
            # pois = dataset_resp.json()
            # return pois
            
            # For demo purposes, return mock data
            mock_pois = self._get_mock_pois(location)
            return json.dumps(mock_pois)
            
        except Exception as e:
            logger.error(f"Error calling Apify API: {e}")
            return f"Error searching for points of interest: {str(e)}"
    
    def _get_mock_pois(self, location: str) -> list:
        """Generate mock POI data for demo purposes."""
        location_lower = location.lower()
        
        if "paris" in location_lower:
            return [
                {
                    "name": "Eiffel Tower",
                    "type": "attraction",
                    "location": "Paris, France",
                    "rating": "4.5",
                    "reviews": 140253,
                    "description": "Iconic symbol of Paris with panoramic city views from observation decks. Pre-booking tickets recommended to avoid long lines."
                },
                {
                    "name": "Louvre Museum",
                    "type": "attraction",
                    "location": "Paris, France",
                    "rating": "4.7",
                    "reviews": 98742,
                    "description": "World's largest art museum housing thousands of works including the Mona Lisa and Venus de Milo. Allow at least half a day to explore highlights."
                },
                {
                    "name": "Notre-Dame Cathedral",
                    "type": "attraction",
                    "location": "Paris, France",
                    "rating": "4.5",
                    "reviews": 85631,
                    "description": "Gothic masterpiece currently under reconstruction after the 2019 fire. The plaza has reopened with a special viewing platform to observe restoration work."
                },
                {
                    "name": "Le Jules Verne",
                    "type": "restaurant",
                    "location": "Paris, France",
                    "rating": "4.6",
                    "reviews": 3452,
                    "description": "Upscale restaurant located on the second floor of the Eiffel Tower offering contemporary French cuisine and spectacular views of Paris."
                },
                {
                    "name": "Seine River Cruise",
                    "type": "activity",
                    "location": "Paris, France",
                    "rating": "4.4",
                    "reviews": 42158,
                    "description": "Relaxing boat tour along the Seine River offering unique views of Paris landmarks. Evening cruises feature illuminated monuments and bridges."
                }
            ]
        elif "tokyo" in location_lower:
            return [
                {
                    "name": "Tokyo Skytree",
                    "type": "attraction",
                    "location": "Tokyo, Japan",
                    "rating": "4.5",
                    "reviews": 25678,
                    "description": "Tallest tower in Japan offering panoramic views of Tokyo from its observation decks. Houses shopping and dining facilities at its base."
                },
                {
                    "name": "Sensō-ji Temple",
                    "type": "attraction",
                    "location": "Tokyo, Japan",
                    "rating": "4.6",
                    "reviews": 38742,
                    "description": "Ancient Buddhist temple in Asakusa with a grand entrance gate (Kaminarimon) and shopping street (Nakamise). Tokyo's oldest temple and a major cultural site."
                },
                {
                    "name": "Tsukiji Outer Market",
                    "type": "attraction",
                    "location": "Tokyo, Japan",
                    "rating": "4.4",
                    "reviews": 15987,
                    "description": "Famous market area with numerous shops and restaurants selling fresh seafood and other Japanese delicacies. Great for breakfast and food exploration."
                },
                {
                    "name": "Sushi Dai",
                    "type": "restaurant",
                    "location": "Tokyo, Japan",
                    "rating": "4.8",
                    "reviews": 3254,
                    "description": "Renowned sushi restaurant formerly in the inner Tsukiji market, now relocated near the outer market. Known for its fresh, high-quality omakase courses."
                },
                {
                    "name": "TeamLab Borderless",
                    "type": "activity",
                    "location": "Tokyo, Japan",
                    "rating": "4.7",
                    "reviews": 12345,
                    "description": "Digital art museum creating immersive, interactive art experiences without boundaries. Exhibits change and interact with visitors and other artworks."
                }
            ]
        elif "berlin" in location_lower:
            return [
                {
                    "name": "Brandenburg Gate",
                    "type": "attraction",
                    "location": "Berlin, Germany",
                    "rating": "4.7",
                    "reviews": 45321,
                    "description": "Iconic 18th-century neoclassical monument and symbol of German unity. Historic site where the Berlin Wall once divided the city."
                },
                {
                    "name": "Reichstag Building",
                    "type": "attraction",
                    "location": "Berlin, Germany",
                    "rating": "4.6",
                    "reviews": 35689,
                    "description": "Historic parliament building with a glass dome offering panoramic views of Berlin. Free to visit but advance registration required."
                },
                {
                    "name": "Berlin Wall Memorial",
                    "type": "attraction",
                    "location": "Berlin, Germany",
                    "rating": "4.8",
                    "reviews": 28975,
                    "description": "Open-air exhibit along former border strip preserving a section of the Berlin Wall. Historical displays chronicle the division of the city."
                },
                {
                    "name": "Curry 36",
                    "type": "restaurant",
                    "location": "Berlin, Germany",
                    "rating": "4.4",
                    "reviews": 12458,
                    "description": "Popular street food stand serving Berlin's famous currywurst. A must-try local culinary experience with multiple locations around the city."
                },
                {
                    "name": "Alternative Berlin Tour",
                    "type": "activity",
                    "location": "Berlin, Germany",
                    "rating": "4.9",
                    "reviews": 8752,
                    "description": "Walking tour exploring Berlin's underground culture, street art, and alternative neighborhoods. Provides insights into the city's creative scene."
                }
            ]
        else:
            return [
                {
                    "name": f"Main Attraction in {location}",
                    "type": "attraction",
                    "location": location,
                    "rating": "4.5",
                    "reviews": 10000,
                    "description": f"The most popular tourist destination in {location}, known for its historical significance and beautiful architecture."
                },
                {
                    "name": f"Top Museum in {location}",
                    "type": "attraction",
                    "location": location,
                    "rating": "4.6",
                    "reviews": 8500,
                    "description": f"A world-class museum featuring artifacts and artwork representing the cultural heritage of {location}."
                },
                {
                    "name": f"Famous Restaurant in {location}",
                    "type": "restaurant",
                    "location": location,
                    "rating": "4.7",
                    "reviews": 3200,
                    "description": f"A highly-rated dining establishment serving authentic local cuisine and specialties from {location}."
                }
            ]