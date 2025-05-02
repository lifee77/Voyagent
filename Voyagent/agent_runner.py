import os
import json
import logging
from dotenv import load_dotenv
# Import the correct modules
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI  # Changed to use Gemini

# Import tool implementations
from Voyagent.tools.perplexity import PerplexitySearchTool
from Voyagent.tools.apify import ApifyFlightTool, ApifyPOITool, ApifyGoogleMapsTool
from Voyagent.tools.deepl import DeepLTranslateTool
from Voyagent.tools.vapi import VapiReservationTool
from Voyagent.tools.gemini_preprocessor import GeminiPreprocessor
from Voyagent.cache_manager import save_to_cache, get_from_cache

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Print the API key (first few characters) for debugging
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    logger.info(f"Google API key loaded: {api_key[:8]}...")
else:
    logger.error("Failed to load GOOGLE_API_KEY from environment")

# System prompt
SYSTEM_PROMPT = """You are a helpful Trip Assistant bot that helps users plan their travel.
You have access to these tools:

1. Perplexity Search - Use this to search for general travel information, current events, or anything that needs up-to-date information
2. Apify Flight Finder - Use this to find flight information when users ask about travel between cities
3. Apify Points of Interest - Use this to find attractions, restaurants, and activities in a destination
4. Apify Google Maps - Use this to find directions, transportation options, or specific places on a map
5. DeepL Translate - Use this to translate text if the user asks for information in a different language
6. Vapi Reservation - Use this to make actual phone calls to book restaurants, hotels, attractions, or contact travel agents when the user explicitly requests to make a reservation or booking

When the user asks a travel-related question:
- If they ask about flights, use the Apify Flight Finder tool
- If they ask about things to do, places to visit, or attractions, use the Apify Points of Interest tool
- For directions or transportation between places, use the Apify Google Maps tool
- For general information about a destination, use Perplexity Search
- If the user mentions a language or asks for translation, use the DeepL Translate tool
- If the user explicitly asks to book or make a reservation, use the Vapi Reservation tool to make phone calls on their behalf

For the Vapi Reservation tool:
- Only use it when a user specifically asks to make a booking or reservation
- You'll need to collect complete information like restaurant/hotel name, phone number, date, time, number of people, and user name
- The tool makes actual phone calls, so only use it for legitimate booking requests

Store important information about the user's trip in their session for later summarization.
Be concise and helpful. Always provide clear, actionable travel advice.

The current date is May 2, 2025.
"""

# Initialize LLM with Google Gemini API key
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",  # Updated to use latest Gemini model
    temperature=0,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

# Initialize Gemini preprocessor
preprocessor = GeminiPreprocessor()

# Initialize tools
tools = [
    PerplexitySearchTool(),
    ApifyFlightTool(),
    ApifyPOITool(),
    ApifyGoogleMapsTool(),
    DeepLTranslateTool(),
    VapiReservationTool()
]

# Dictionary to store user chat history and context
user_sessions = {}

def get_tool_by_name(tool_name):
    """Get a tool instance by its name."""
    for tool in tools:
        if tool.name == tool_name:
            return tool
    return None

def process_message(message, user_info):
    """Process a message using Gemini preprocessing, tools, and LLM for response generation"""
    user_id = user_info['id']
    
    # Initialize user session if it doesn't exist
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "chat_history": [],
            "trip_info": {}
        }
    
    # Execute conversation
    logger.info(f"Processing message from User {user_id}: {message}")
    try:
        # Step 1: Preprocess the query with Gemini
        structured_query = preprocessor.preprocess_query(message)
        query_type = structured_query.get("query_type", "general")
        
        logger.info(f"Preprocessed query type: {query_type}")
        
        # Step 2: Select the appropriate tool based on the structured query
        tool_to_use = None
        
        if query_type == "flight":
            tool_to_use = get_tool_by_name("apify_flight")
            # Use preprocessed data for better tool input
            origin, destination, date = preprocessor.extract_travel_info(message)
            if origin and destination:
                message = f"from: {origin}, to: {destination}" + (f", date: {date}" if date else "")
                logger.info(f"Structured flight query: {message}")
                
        elif query_type == "poi" or query_type == "recommendations":
            tool_to_use = get_tool_by_name("apify_poi")
            # Use the destination for POI search
            if structured_query.get("destination"):
                message = structured_query.get("destination")
                logger.info(f"Structured POI query: {message}")
                
        elif query_type == "directions":
            tool_to_use = get_tool_by_name("apify_google_maps")
            # Format as directions query
            origin = structured_query.get("origin", "")
            destination = structured_query.get("destination", "")
            if origin and destination:
                message = f"directions from {origin} to {destination}"
                logger.info(f"Structured directions query: {message}")
                
        # Check for other specific tool needs
        if "translate" in message.lower() or any(lang in message.lower() for lang in ["spanish", "french", "german", "japanese"]):
            tool_to_use = get_tool_by_name("deepl_translate")
        
        elif any(term in message.lower() for term in ["book", "reserve", "reservation", "call"]):
            tool_to_use = get_tool_by_name("vapi_reservation")
        
        # Fallback to Perplexity for general queries
        if not tool_to_use and query_type == "general":
            tool_to_use = get_tool_by_name("perplexity_search")
            # Use the optimized query if available
            if "structured_query" in structured_query:
                message = structured_query.get("structured_query")
        
        # Step 3: Execute the selected tool
        if tool_to_use:
            logger.info(f"Using tool: {tool_to_use.name}")
            
            # Special handling for reservation tool
            if tool_to_use.name == "vapi_reservation":
                prompt = f"""Based on this request: "{message}"
                
                Create a JSON structure for making a reservation with these fields:
                - service_type: "restaurant", "hotel", "attraction" or "travel_agent"
                - service_name: Name of the business
                - phone_number: Phone number with country code
                - user_name: The name for the reservation
                - reservation_details: Include date, time (if applicable), number of people, and any special requests
                
                Return ONLY the JSON without explanation:"""
                
                messages = [
                    SystemMessage(content="You are a helpful assistant that creates structured JSON data."),
                    HumanMessage(content=prompt)
                ]
                
                structured_input = llm.invoke(messages).content
                
                try:
                    # Extract JSON from the response
                    json_start = structured_input.find("{")
                    json_end = structured_input.rfind("}") + 1
                    if json_start >= 0 and json_end > 0:
                        json_str = structured_input[json_start:json_end]
                        tool_response = tool_to_use._run(json_str)
                    else:
                        tool_response = "I couldn't process your reservation request. Could you provide more details about what you'd like to book?"
                except Exception as e:
                    logger.error(f"Error processing reservation: {e}")
                    tool_response = "I encountered an error processing your reservation. Please try again with more details."
            else:
                # For other tools, pass the processed message
                tool_response = tool_to_use._run(message)
            
            # Step 4: Process the tool response with LLM to create a conversational reply
            # Include the original query and structured data for context
            response_prompt = f"""Based on this user question: "{message}"
            
            And this tool response:
            "{tool_response}"
            
            Structured data about the query:
            {json.dumps(structured_query)}
            
            Create a helpful, conversational response. Include the most relevant information from the tool output but make it sound natural and conversational. If the tool returned structured data, format it in a readable way.
            
            If the query was about traveling to Yosemite, be sure to mention transportation options from nearby cities if relevant."""
            
            response_messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=response_prompt)
            ]
            
            final_response = llm.invoke(response_messages).content
            
            # Create structured_result with needed fields
            structured_result = {
                "output": final_response,
                "intermediate_steps": [
                    {
                        "tool_name": tool_to_use.name, 
                        "tool_input": message, 
                        "tool_output": tool_response,
                        "structured_data": structured_query
                    }
                ]
            }
            
        else:
            # Fallback to direct LLM conversation
            chat_history = user_sessions[user_id]["chat_history"]
            
            # Prepare messages for the LLM
            messages = [SystemMessage(content=SYSTEM_PROMPT)]
            
            # Add the last few messages from chat history (if any)
            if chat_history:
                messages.extend(chat_history[-6:])  # Add up to 3 turns of conversation (6 messages)
            
            # Add the current user message and structured data
            enhanced_message = f"""User message: {message}
            
            Structured data about the message:
            {json.dumps(structured_query)}
            """
            messages.append(HumanMessage(content=enhanced_message))
            
            # Get response from LLM
            final_response = llm.invoke(messages).content
            
            structured_result = {
                "output": final_response,
                "intermediate_steps": [],
                "structured_data": structured_query
            }
        
        # Update chat history
        user_sessions[user_id]["chat_history"].append(HumanMessage(content=message))
        user_sessions[user_id]["chat_history"].append(AIMessage(content=final_response))
        
        # Extract and cache important travel information
        save_to_cache(user_id, message, structured_result)
        
        return final_response
    
    except Exception as e:
        logger.error(f"Error in message processing: {e}", exc_info=True)
        return "I encountered an error while processing your request. Please try again."