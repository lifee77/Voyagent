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
        from_city = params["from"].lower() if params["from"] else ""
        to_city = params["to"].lower() if params["to"] else ""
        
        # Handle cases where the query doesn't have clear from/to parameters
        if not from_city or not to_city:
            # Try to extract locations from the original query
            query_lower = " ".join(params.values()).lower()
            
            if "yosemite" in query_lower:
                # Default to San Francisco to Fresno (nearest airport to Yosemite)
                if "san francisco" in query_lower or "sf" in query_lower:
                    from_city = "san francisco"
                    to_city = "fresno"
                else:
                    # Default case for Yosemite queries
                    from_city = "san francisco"
                    to_city = "fresno"
        
        # New York to London flights
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
                    "stops": 0
                },
                {
                    "airline": "American Airlines",
                    "flightNumber": "AA100",
                    "departureAirport": "JFK",
                    "arrivalAirport": "LHR",
                    "departureCity": "New York",
                    "arrivalCity": "London",
                    "departureDate": "2025-05-15T18:00:00",
                    "arrivalDate": "2025-05-16T06:30:00",
                    "duration": "7h 30m",
                    "price": "$698",
                    "stops": 0
                }
            ]
        # San Francisco to Fresno/Yosemite flights
        elif ("san francisco" in from_city or "sf" in from_city) and ("fresno" in to_city or "yosemite" in to_city):
            return [
                {
                    "airline": "United Airlines",
                    "flightNumber": "UA5568",
                    "departureAirport": "SFO",
                    "arrivalAirport": "FAT",
                    "departureCity": "San Francisco",
                    "arrivalCity": "Fresno (Yosemite Intl)",
                    "departureDate": "2025-05-12T08:30:00",
                    "arrivalDate": "2025-05-12T09:45:00",
                    "duration": "1h 15m",
                    "price": "$159",
                    "stops": 0
                },
                {
                    "airline": "American Airlines",
                    "flightNumber": "AA5844",
                    "departureAirport": "SFO",
                    "arrivalAirport": "FAT",
                    "departureCity": "San Francisco",
                    "arrivalCity": "Fresno (Yosemite Intl)",
                    "departureDate": "2025-05-13T10:15:00",
                    "arrivalDate": "2025-05-13T11:30:00",
                    "duration": "1h 15m",
                    "price": "$178",
                    "stops": 0
                }
            ]
        # Default mock data for any other route
        else:
            return [
                {
                    "message": "No direct flights found for this route. Consider checking alternative airports or transportation options.",
                    "alternatives": [
                        {
                            "type": "Note",
                            "description": f"For travel to Yosemite National Park from San Francisco, flying to Fresno (FAT) is the closest option, followed by a rental car or bus service."
                        },
                        {
                            "type": "Ground Transportation",
                            "description": "YARTS (Yosemite Area Regional Transportation System) offers bus service from various cities to Yosemite."
                        }
                    ]
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


class ApifyGoogleMapsTool(BaseTool):
    name = "apify_google_maps"
    description = """
    Uses Apify Google Maps Scraper actor to search for places like restaurants, attractions, or businesses.
    Provides details such as ratings, reviews, driving times, and images.
    
    Input should be in the format: "type: [place type], location: [location], query: [optional search terms]"
    Example: "type: restaurant, location: New York, query: Italian food"
    """
    
    def _run(self, query: str) -> str:
        """Run Apify Google Maps Scraper with the given parameters."""
        logger.info(f"TOOL: apify_google_maps - Query: {query}")
        
        api_token = os.getenv("APIFY_API_TOKEN")
        if not api_token:
            logger.error("Apify API token not found")
            return "Error: Apify API token not configured"
        
        # Parse query to extract parameters
        params = self._parse_maps_query(query)
        
        # In a real implementation, call the Apify Google Maps Scraper actor
        # actor_id = "apify/google-maps-scraper"
        # url = f"https://api.apify.com/v2/acts/{actor_id}/runs"
        
        # headers = {
        #     "Authorization": f"Bearer {api_token}",
        #     "Content-Type": "application/json"
        # }
        
        # payload = {
        #     "searchString": f"{params.get('query', '')} {params.get('type', '')} in {params.get('location', '')}".strip(),
        #     "maxCrawledPlaces": 10,
        #     "includeReviews": True,
        #     "includeImages": True,
        #     "language": "en"
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
            # places = dataset_resp.json()
            # return places
            
            # For demo purposes, return mock data
            mock_places = self._get_mock_places(params)
            return json.dumps(mock_places)
            
        except Exception as e:
            logger.error(f"Error calling Apify API: {e}")
            return f"Error searching for places: {str(e)}"
    
    def _parse_maps_query(self, query: str) -> dict:
        """Parse the query to extract parameters."""
        params = {"type": "", "location": "", "query": ""}
        
        for part in query.split(","):
            part = part.strip().lower()
            
            if part.startswith("type:"):
                params["type"] = part[5:].strip()
            elif part.startswith("location:"):
                params["location"] = part[9:].strip()
            elif part.startswith("query:"):
                params["query"] = part[6:].strip()
        
        return params
    
    def _get_mock_places(self, params: dict) -> list:
        """Generate mock place data for demo purposes."""
        place_type = params.get("type", "").lower()
        location = params.get("location", "").lower()
        query = params.get("query", "").lower()
        
        # Restaurant search
        if "restaurant" in place_type:
            if "new york" in location:
                if "italian" in query:
                    return [
                        {
                            "name": "Carbone",
                            "address": "181 Thompson St, New York, NY 10012",
                            "rating": 4.7,
                            "totalReviews": 3452,
                            "priceLevel": "$$$",
                            "category": "Italian restaurant",
                            "openingHours": "5:00 PM - 11:00 PM",
                            "phoneNumber": "(212) 254-3000",
                            "website": "https://www.carbonenewyork.com",
                            "description": "Upscale Italian-American restaurant known for its tableside service and classic dishes.",
                            "popularDishes": ["Spicy Rigatoni Vodka", "Veal Parmesan", "Caesar Salad"],
                            "drivingTime": {
                                "from": "Times Square",
                                "duration": "15 minutes",
                                "distance": "2.1 miles"
                            },
                            "images": [
                                "https://example.com/carbone_interior.jpg",
                                "https://example.com/carbone_food1.jpg",
                                "https://example.com/carbone_food2.jpg"
                            ],
                            "reviews": [
                                {
                                    "text": "Amazing atmosphere and the spicy rigatoni is to die for!",
                                    "rating": 5,
                                    "author": "John D."
                                },
                                {
                                    "text": "Classic New York Italian experience. Expensive but worth it for a special occasion.",
                                    "rating": 5,
                                    "author": "Maria L."
                                }
                            ]
                        },
                        {
                            "name": "Lilia",
                            "address": "567 Union Ave, Brooklyn, NY 11222",
                            "rating": 4.8,
                            "totalReviews": 2897,
                            "priceLevel": "$$$",
                            "category": "Italian restaurant",
                            "openingHours": "5:30 PM - 10:30 PM",
                            "phoneNumber": "(718) 576-3095",
                            "website": "https://www.lilianewyork.com",
                            "description": "Modern Italian restaurant in a converted auto body shop with handmade pasta.",
                            "popularDishes": ["Sheep's Milk Cheese Filled Agnolotti", "Grilled Clams", "Cacio e Pepe Fritelle"],
                            "drivingTime": {
                                "from": "Times Square",
                                "duration": "25 minutes",
                                "distance": "5.8 miles"
                            },
                            "images": [
                                "https://example.com/lilia_interior.jpg",
                                "https://example.com/lilia_pasta1.jpg",
                                "https://example.com/lilia_pasta2.jpg"
                            ],
                            "reviews": [
                                {
                                    "text": "Best pasta I've had outside of Italy. The agnolotti is incredible.",
                                    "rating": 5,
                                    "author": "Sophie R."
                                },
                                {
                                    "text": "Worth the wait to get a reservation. The atmosphere and food are both exceptional.",
                                    "rating": 4,
                                    "author": "Michael T."
                                }
                            ]
                        }
                    ]
            elif "tokyo" in location:
                if "sushi" in query or query == "":
                    return [
                        {
                            "name": "Sukiyabashi Jiro",
                            "address": "4 Chome-2-15 Ginza, Chuo City, Tokyo",
                            "rating": 4.9,
                            "totalReviews": 1543,
                            "priceLevel": "$$$$",
                            "category": "Sushi restaurant",
                            "openingHours": "11:30 AM - 2:00 PM, 5:00 PM - 8:00 PM",
                            "phoneNumber": "+81 3-3535-3600",
                            "description": "World-famous sushi restaurant featured in 'Jiro Dreams of Sushi' documentary. Reservations required months in advance.",
                            "popularDishes": ["Omakase Course"],
                            "drivingTime": {
                                "from": "Tokyo Station",
                                "duration": "10 minutes",
                                "distance": "1.2 miles"
                            },
                            "images": [
                                "https://example.com/jiro_interior.jpg",
                                "https://example.com/jiro_sushi1.jpg",
                                "https://example.com/jiro_sushi2.jpg"
                            ],
                            "reviews": [
                                {
                                    "text": "Once-in-a-lifetime dining experience. The precision and care put into each piece is extraordinary.",
                                    "rating": 5,
                                    "author": "David L."
                                },
                                {
                                    "text": "The best sushi I've ever had. Simple, pure, and perfect.",
                                    "rating": 5,
                                    "author": "Emma K."
                                }
                            ]
                        },
                        {
                            "name": "Sushi Saito",
                            "address": "1 Chome-4-5 Roppongi, Minato City, Tokyo",
                            "rating": 4.9,
                            "totalReviews": 1287,
                            "priceLevel": "$$$$",
                            "category": "Sushi restaurant",
                            "openingHours": "12:00 PM - 2:00 PM, 5:00 PM - 10:00 PM",
                            "phoneNumber": "+81 3-3589-4412",
                            "description": "Exclusive 3-Michelin-starred sushi restaurant requiring introductions for reservations.",
                            "popularDishes": ["Fatty Tuna", "Sea Urchin", "Omakase Course"],
                            "drivingTime": {
                                "from": "Tokyo Station",
                                "duration": "15 minutes",
                                "distance": "2.5 miles"
                            },
                            "images": [
                                "https://example.com/saito_interior.jpg",
                                "https://example.com/saito_sushi1.jpg",
                                "https://example.com/saito_sushi2.jpg"
                            ],
                            "reviews": [
                                {
                                    "text": "Chef Saito's attention to detail and the quality of fish is unmatched.",
                                    "rating": 5,
                                    "author": "James W."
                                },
                                {
                                    "text": "The rice temperature and seasoning are perfect. Worth every penny.",
                                    "rating": 5,
                                    "author": "Yuki T."
                                }
                            ]
                        }
                    ]
            else:
                # Generic restaurant results for any other location
                return [
                    {
                        "name": f"Top Restaurant in {location.title()}",
                        "address": f"123 Main St, {location.title()}",
                        "rating": 4.7,
                        "totalReviews": 1245,
                        "priceLevel": "$$$",
                        "category": f"{query if query else 'Local'} restaurant",
                        "openingHours": "11:00 AM - 10:00 PM",
                        "phoneNumber": "(555) 123-4567",
                        "website": "https://www.example.com/restaurant",
                        "description": f"A highly-rated {query if query else 'local'} dining spot in {location.title()} known for exceptional service and cuisine.",
                        "popularDishes": ["Signature Dish 1", "Signature Dish 2", "Special Dessert"],
                        "drivingTime": {
                            "from": "City Center",
                            "duration": "10 minutes",
                            "distance": "1.5 miles"
                        },
                        "images": [
                            "https://example.com/restaurant_interior.jpg",
                            "https://example.com/restaurant_food1.jpg",
                            "https://example.com/restaurant_food2.jpg"
                        ],
                        "reviews": [
                            {
                                "text": "Exceptional atmosphere and even better food. Highly recommended!",
                                "rating": 5,
                                "author": "Local Reviewer"
                            },
                            {
                                "text": "Great service and delicious food. Will definitely come back.",
                                "rating": 4,
                                "author": "Tourist Reviewer"
                            }
                        ]
                    },
                    {
                        "name": f"Popular Café in {location.title()}",
                        "address": f"456 Oak St, {location.title()}",
                        "rating": 4.5,
                        "totalReviews": 982,
                        "priceLevel": "$$",
                        "category": "Café",
                        "openingHours": "7:00 AM - 8:00 PM",
                        "phoneNumber": "(555) 987-6543",
                        "website": "https://www.example.com/cafe",
                        "description": f"A charming café with great ambiance and variety of {query if query else 'local'} specialties.",
                        "popularDishes": ["Breakfast Special", "House Coffee", "Signature Pastry"],
                        "drivingTime": {
                            "from": "City Center",
                            "duration": "8 minutes",
                            "distance": "1.2 miles"
                        },
                        "images": [
                            "https://example.com/cafe_interior.jpg",
                            "https://example.com/cafe_food1.jpg",
                            "https://example.com/cafe_food2.jpg"
                        ],
                        "reviews": [
                            {
                                "text": "Perfect spot for breakfast or lunch. The coffee is excellent!",
                                "rating": 5,
                                "author": "Coffee Lover"
                            },
                            {
                                "text": "Great place to work remotely. Good food and relaxed atmosphere.",
                                "rating": 4,
                                "author": "Digital Nomad"
                            }
                        ]
                    }
                ]
        
        # Attractions/Landmarks search
        elif "attraction" in place_type or "landmark" in place_type:
            if "paris" in location:
                return [
                    {
                        "name": "Eiffel Tower",
                        "address": "Champ de Mars, 5 Avenue Anatole France, 75007 Paris",
                        "rating": 4.6,
                        "totalReviews": 145782,
                        "category": "Landmark",
                        "openingHours": "9:00 AM - 11:45 PM",
                        "phoneNumber": "+33 892 70 12 39",
                        "website": "https://www.toureiffel.paris/en",
                        "description": "Iconic symbol of Paris, offering panoramic views from multiple observation decks.",
                        "entryFee": "From €17.10 for adults, depending on which floor you visit",
                        "drivingTime": {
                            "from": "Notre Dame",
                            "duration": "15 minutes",
                            "distance": "2.3 miles"
                        },
                        "images": [
                            "https://example.com/eiffel_day.jpg",
                            "https://example.com/eiffel_night.jpg",
                            "https://example.com/eiffel_view.jpg"
                        ],
                        "reviews": [
                            {
                                "text": "Most beautiful at night when it sparkles on the hour. Worth waiting to see.",
                                "rating": 5,
                                "author": "Travel Enthusiast"
                            },
                            {
                                "text": "Long lines but worth it for the view. Book tickets online in advance.",
                                "rating": 4,
                                "author": "Family Traveler"
                            }
                        ]
                    },
                    {
                        "name": "Louvre Museum",
                        "address": "Rue de Rivoli, 75001 Paris",
                        "rating": 4.7,
                        "totalReviews": 124563,
                        "category": "Museum",
                        "openingHours": "9:00 AM - 6:00 PM, Closed Tuesdays",
                        "phoneNumber": "+33 1 40 20 53 17",
                        "website": "https://www.louvre.fr/en",
                        "description": "World's largest art museum and home to thousands of works including the Mona Lisa.",
                        "entryFee": "€17 for adults, free for under 18s",
                        "drivingTime": {
                            "from": "Eiffel Tower",
                            "duration": "15 minutes",
                            "distance": "2.5 miles"
                        },
                        "images": [
                            "https://example.com/louvre_pyramid.jpg",
                            "https://example.com/louvre_monalisa.jpg",
                            "https://example.com/louvre_gallery.jpg"
                        ],
                        "reviews": [
                            {
                                "text": "Overwhelming in size. Plan at least half a day and focus on specific sections.",
                                "rating": 5,
                                "author": "Art Lover"
                            },
                            {
                                "text": "The Mona Lisa is smaller than you'd expect and crowded. Many other amazing pieces to see.",
                                "rating": 4,
                                "author": "History Buff"
                            }
                        ]
                    }
                ]
            else:
                # Generic attraction results
                return [
                    {
                        "name": f"Main Attraction in {location.title()}",
                        "address": f"100 Tourist Avenue, {location.title()}",
                        "rating": 4.7,
                        "totalReviews": 15782,
                        "category": "Landmark",
                        "openingHours": "9:00 AM - 6:00 PM",
                        "phoneNumber": "(555) 234-5678",
                        "website": "https://www.example.com/attraction",
                        "description": f"The most visited landmark in {location.title()}, known for its historical significance and beautiful architecture.",
                        "entryFee": "$15 for adults, $10 for children",
                        "drivingTime": {
                            "from": "City Center",
                            "duration": "12 minutes",
                            "distance": "2.1 miles"
                        },
                        "images": [
                            "https://example.com/attraction_exterior.jpg",
                            "https://example.com/attraction_interior.jpg",
                            "https://example.com/attraction_detail.jpg"
                        ],
                        "reviews": [
                            {
                                "text": "A must-visit when in the area. The architecture is stunning.",
                                "rating": 5,
                                "author": "History Enthusiast"
                            },
                            {
                                "text": "Worth the entrance fee. Plan to spend at least 2 hours exploring.",
                                "rating": 4,
                                "author": "Travel Blogger"
                            }
                        ]
                    },
                    {
                        "name": f"Popular Museum in {location.title()}",
                        "address": f"200 Culture Street, {location.title()}",
                        "rating": 4.6,
                        "totalReviews": 8943,
                        "category": "Museum",
                        "openingHours": "10:00 AM - 5:00 PM, Closed Mondays",
                        "phoneNumber": "(555) 876-5432",
                        "website": "https://www.example.com/museum",
                        "description": f"A fascinating collection showcasing the history and culture of {location.title()}.",
                        "entryFee": "$12 for adults, free for children under 12",
                        "drivingTime": {
                            "from": "City Center",
                            "duration": "10 minutes",
                            "distance": "1.8 miles"
                        },
                        "images": [
                            "https://example.com/museum_exterior.jpg",
                            "https://example.com/museum_exhibit1.jpg",
                            "https://example.com/museum_exhibit2.jpg"
                        ],
                        "reviews": [
                            {
                                "text": "Excellent curation and informative displays. The guided tour is worth it.",
                                "rating": 5,
                                "author": "Culture Enthusiast"
                            },
                            {
                                "text": "Kid-friendly with interactive exhibits. Great for families.",
                                "rating": 4,
                                "author": "Family Traveler"
                            }
                        ]
                    }
                ]
        
        # Default generic places
        else:
            return [
                {
                    "name": f"{place_type.title() if place_type else 'Popular Place'} in {location.title()}",
                    "address": f"123 Main Street, {location.title()}",
                    "rating": 4.5,
                    "totalReviews": 1000,
                    "category": place_type.title() if place_type else "Point of Interest",
                    "description": f"A popular {place_type if place_type else 'destination'} in {location.title()}.",
                    "drivingTime": {
                        "from": "City Center",
                        "duration": "10 minutes",
                        "distance": "1.5 miles"
                    },
                    "images": [
                        "https://example.com/place_exterior.jpg",
                        "https://example.com/place_interior.jpg"
                    ],
                    "reviews": [
                        {
                            "text": f"Great {place_type if place_type else 'place'} to visit in {location.title()}.",
                            "rating": 4,
                            "author": "Local Guide"
                        }
                    ]
                },
                {
                    "name": f"Another {place_type.title() if place_type else 'Interesting Spot'} in {location.title()}",
                    "address": f"456 Side Street, {location.title()}",
                    "rating": 4.3,
                    "totalReviews": 850,
                    "category": place_type.title() if place_type else "Point of Interest",
                    "description": f"Another highly rated {place_type if place_type else 'location'} worth visiting in {location.title()}.",
                    "drivingTime": {
                        "from": "City Center",
                        "duration": "15 minutes",
                        "distance": "2.2 miles"
                    },
                    "images": [
                        "https://example.com/another_place_exterior.jpg",
                        "https://example.com/another_place_detail.jpg"
                    ],
                    "reviews": [
                        {
                            "text": f"Hidden gem in {location.title()}. Less crowded than the main spots.",
                            "rating": 5,
                            "author": "Experienced Traveler"
                        }
                    ]
                }
            ]