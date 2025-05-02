import os
import requests
import logging
from dotenv import load_dotenv
from langchain.tools import BaseTool

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class PerplexitySearchTool(BaseTool):
    name = "perplexity_search"
    description = """
    Searches the web using Perplexity Sonar API for up-to-date information about travel destinations,
    events, weather, or any other travel-related information. Use this for general travel questions.
    
    Input should be a clear search query related to travel information.
    """
    
    def _run(self, query: str) -> str:
        """Run Perplexity search with the given query."""
        logger.info(f"TOOL: perplexity_search - Query: {query}")
        
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            logger.error("Perplexity API key not found")
            return "Error: Perplexity API key not configured"
        
        # In a real implementation, call the Perplexity Sonar API
        url = "https://api.perplexity.ai/search"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "query": query,
            "max_results": 5
        }
        
        try:
            # Uncomment to actually call the API
            # response = requests.post(url, headers=headers, json=data)
            # response.raise_for_status()
            # result = response.json()
            # return result
            
            # For demo purposes, return mock data
            mock_result = self._get_mock_result(query)
            return mock_result
            
        except Exception as e:
            logger.error(f"Error calling Perplexity API: {e}")
            return f"Error searching Perplexity: {str(e)}"
    
    def _get_mock_result(self, query: str) -> str:
        """Generate mock search results for demo purposes."""
        query_lower = query.lower()
        
        if "berlin" in query_lower:
            return """
            Information about Berlin (as of May 2025):
            
            1. Popular attractions in Berlin include the Brandenburg Gate, Reichstag Building, Berlin Wall Memorial, Museum Island, and Checkpoint Charlie.
            
            2. The weather in Berlin in May is generally pleasant with average temperatures between 12°C and 21°C (54°F to 70°F).
            
            3. Currently, Berlin is hosting several events in May 2025, including:
               - Berlin Gallery Weekend (May 1-3, 2025)
               - Berlin Marathon (May 15, 2025)
               - International Museum Day celebrations (May 18, 2025)
            
            4. Transportation in Berlin is efficient with the U-Bahn (subway), S-Bahn (suburban trains), buses, and trams. Consider getting a Berlin WelcomeCard for unlimited travel and discounts.
            
            5. Some highly-rated restaurants include Nobelhart & Schmutzig (modern German), CODA Dessert Bar (innovative desserts), and Markthalle Neun's Street Food Thursday (various cuisines).
            
            Sources:
            - Visit Berlin Official Tourism Site (visited May 2, 2025)
            - Berlin Events Calendar 2025 (visited May 2, 2025)
            - Weather Underground Historical Data (visited May 2, 2025)
            """
        elif "tokyo" in query_lower:
            return """
            Information about Tokyo (as of May 2025):
            
            1. Tokyo is currently experiencing beautiful spring weather with cherry blossoms in late bloom in some northern areas. Temperatures average 15°C to 23°C (59°F to 73°F).
            
            2. Key attractions include Tokyo Skytree, Meiji Shrine, Sensō-ji Temple, Shibuya Crossing, and the Imperial Palace Gardens.
            
            3. Notable May 2025 events include:
               - Tokyo Game Show Spring (May 5-7, 2025)
               - Sanja Matsuri Festival in Asakusa (May 16-18, 2025)
               - Neo-Japonism Art Exhibition (All month)
            
            4. The Tokyo Metro and JR lines provide extensive public transportation. Consider a PASMO or Suica card for convenience.
            
            5. Current travel advisories: None major, but note that some areas still have enhanced health screening procedures.
            
            Sources:
            - Japan National Tourism Organization (visited May 2, 2025)
            - Tokyo Metropolitan Government (visited May 2, 2025)
            - Japan Meteorological Agency (visited May 2, 2025)
            """
        elif "paris" in query_lower:
            return """
            Information about Paris (as of May 2025):
            
            1. Paris in May has mild temperatures ranging from 11°C to 20°C (52°F to 68°F) with occasional rain showers.
            
            2. Must-see attractions include the Eiffel Tower, Louvre Museum, Notre-Dame Cathedral (reconstruction viewing), Arc de Triomphe, and Montmartre.
            
            3. Current events in May 2025:
               - French Open Tennis Tournament at Roland Garros (May 25 - June 8, 2025)
               - Nuit des Musées (Museum Night) on May 17, 2025
               - Paris Art Fair at Grand Palais (May 9-12, 2025)
            
            4. The Paris Metro, RER trains, and bus system offer comprehensive public transportation. The Paris Visite pass provides unlimited travel.
            
            5. Notre-Dame Cathedral remains partially closed for reconstruction following the 2019 fire, but the plaza in front has reopened with a viewing platform.
            
            Sources:
            - Paris Convention and Visitors Bureau (visited May 2, 2025)
            - Météo-France (visited May 2, 2025)
            - Roland Garros Official Site (visited May 2, 2025)
            """
        else:
            return """
            General Travel Information (as of May 2025):
            
            1. Current global travel trends show increased interest in sustainable tourism and off-the-beaten-path destinations.
            
            2. Popular destinations for May 2025 travel include Mediterranean coastal cities, Japan for late cherry blossom season, and northern Europe as it warms up.
            
            3. Several international festivals occurring in May 2025:
               - Cannes Film Festival (France, May 13-24, 2025)
               - Monaco Grand Prix (Monaco, May 22-25, 2025)
               - Chelsea Flower Show (London, May 20-24, 2025)
            
            4. Travel technology trends include increased use of digital passports, AI travel assistants, and contact-free hotel experiences.
            
            5. Current travel advisories: Always check your government's official travel advisories before booking international trips.
            
            Sources:
            - World Tourism Organization (visited May 2, 2025)
            - International Air Transport Association (visited May 2, 2025)
            - Various tourism board websites (visited May 2, 2025)
            """