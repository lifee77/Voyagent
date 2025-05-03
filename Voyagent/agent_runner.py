import os
import json
import logging
import time
import asyncio
from dotenv import load_dotenv
# Import the correct modules
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI  # Changed to use Gemini

# Import tool implementations
from Voyagent.tools.perplexity import PerplexitySearchTool
from Voyagent.tools.apify import ApifyFlightTool, ApifyPOITool, ApifyGoogleMapsTool
from Voyagent.tools.deepl import DeepLTranslateTool
from Voyagent.tools.vapi import VapiReservationTool, VapiCallTool
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
    VapiReservationTool(),
    VapiCallTool()
]

# Dictionary to store user chat history and context
user_sessions = {}

# Callback functions for handling telegram updates
telegram_callbacks = {}

def get_tool_by_name(tool_name):
    """Get a tool instance by its name."""
    for tool in tools:
        if tool.name == tool_name:
            return tool
    return None

def register_telegram_callback(callback_func):
    """Register a callback function to send updates to Telegram."""
    telegram_callbacks["send_message"] = callback_func
    logger.info("Registered Telegram callback function")

def update_thought_process(user_id, thought, replace=False):
    """Send thought process updates to Telegram."""
    if "send_message" in telegram_callbacks:
        try:
            # Escape special Markdown characters to prevent parsing errors
            escaped_thought = thought.replace("*", "\\*").replace("_", "\\_").replace("`", "\\`").replace("[", "\\[")
            
            # Prefix the thought to make it clear it's the internal thought process
            formatted_thought = f"🧠 Thought Process: {escaped_thought}"
            
            # Get existing thought message ID for this user if it exists
            message_id = None
            if user_id in user_sessions and "thought_message_id" in user_sessions[user_id]:
                message_id = user_sessions[user_id]["thought_message_id"]
                
            # Send via the callback - use HTML instead of Markdown for more reliable formatting
            result = telegram_callbacks["send_message"](
                user_id, 
                formatted_thought, 
                message_id=message_id if replace else None,
                parse_mode="HTML"  # Using HTML mode instead of Markdown for better reliability
            )
            
            # If this is a new thought message, store its ID
            if replace and result and "message_id" in result:
                if user_id in user_sessions:
                    user_sessions[user_id]["thought_message_id"] = result["message_id"]
            
            return result
        except Exception as e:
            logger.error(f"Error sending thought process to Telegram: {e}")
            # If there was an error, try sending without parse mode
            try:
                result = telegram_callbacks["send_message"](
                    user_id,
                    f"🧠 Thought Process: {thought}",
                    message_id=message_id if replace else None,
                    parse_mode=""  # No parse mode as fallback
                )
                return result
            except Exception as inner_e:
                logger.error(f"Error sending fallback thought process: {inner_e}")
            return None
    return None

def process_message(message, user_info):
    """Process a message using Gemini preprocessing, tools, and LLM for response generation"""
    user_id = user_info['id']
    
    # Initialize user session if it doesn't exist
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "chat_history": [],
            "trip_info": {},
            "thought_message_id": None
        }
    
    # Execute conversation
    logger.info(f"Processing message from User {user_id}: {message}")
    try:
        # Start thought process display
        update_thought_process(user_id, "Starting to process your query...", replace=True)
        
        # Check for call keywords
        if "call" in message.lower() and any(char.isdigit() for char in message):
            update_thought_process(user_id, "Detected a request to make a phone call...", replace=True)
            call_tool = VapiCallTool()
            response = call_tool._run(message)
            return response
        
        # Step 1: Preprocess the query with Gemini
        update_thought_process(user_id, "Analyzing your query with Gemini to understand your travel needs...", replace=True)
        structured_query = preprocessor.preprocess_query(message)
        query_type = structured_query.get("query_type", "general")
        
        logger.info(f"Preprocessed query type: {query_type}")
        update_thought_process(
            user_id, 
            f"I've identified this as a {query_type} query.\n"
            f"Origin: {structured_query.get('origin', 'Not specified')}\n"
            f"Destination: {structured_query.get('destination', 'Not specified')}\n"
            f"Date: {structured_query.get('date_info', {}).get('start_date', 'Not specified')}",
            replace=True
        )
        
        # Step 2: Select the appropriate tool based on the structured query
        tool_to_use = None
        
        if query_type == "flight":
            tool_to_use = get_tool_by_name("apify_flight")
            update_thought_process(user_id, "Looking for flight information using Skyscanner...", replace=True)
            # Use preprocessed data for better tool input
            origin, destination, date = preprocessor.extract_travel_info(message)
            if origin and destination:
                message = f"from: {origin}, to: {destination}" + (f", date: {date}" if date else "")
                logger.info(f"Structured flight query: {message}")
                update_thought_process(user_id, f"Searching for flights from {origin} to {destination}" + (f" on {date}" if date else ""), replace=True)
        
        elif query_type == "transport_comparison":
            # This is a special case for comparing transportation methods
            update_thought_process(user_id, "Analyzing transportation comparison options...", replace=True)
            
            origin = structured_query.get("origin", "")
            destination = structured_query.get("destination", "")
            transport_modes = structured_query.get("transport_modes", [])
            
            # Use static comparison data for common routes
            if (origin.lower() in ["san francisco", "sf", "bay area"] and 
                destination.lower() in ["yosemite", "yosemite national park"]):
                    
                comparison_data = {
                    "comparison": {
                        "driving": {
                            "route": f"Driving from {origin} to {destination}",
                            "distance": "170-200 miles depending on route",
                            "duration": "3.5-4.5 hours each way",
                            "cost": "$30-40 in gas (estimated)",
                            "advantages": ["Freedom to explore at your own pace", 
                                          "No need for additional transportation in the park",
                                          "Scenic drive through the Sierra Nevada mountains"],
                            "disadvantages": ["Longer travel time than flying to a nearby airport",
                                             "Driver fatigue on mountain roads",
                                             "Seasonal road closures possible (check conditions)"]
                        },
                        "flying": {
                            "route": f"Flying from {origin} to Fresno Yosemite International Airport (FAT)",
                            "details": "1-hour flight + 1.5-hour drive from Fresno to Yosemite Valley",
                            "duration": "Total journey: 3.5-4 hours including airport time",
                            "cost": "$120-250 for flight + $60-100 for car rental per day",
                            "advantages": ["Less direct driving time", 
                                          "Good option if you don't enjoy mountain driving"],
                            "disadvantages": ["Still need to rent a car from Fresno",
                                             "More expensive than driving directly",
                                             "Less flexibility with flight schedules"]
                        },
                        "recommendation": "For trips to Yosemite from San Francisco, driving is generally the preferred option for most visitors. The drive is scenic, especially as you approach the park, and having your own car gives you maximum flexibility to explore different areas of this large park. Flying to Fresno can make sense if you prefer to minimize driving or if your time is limited."
                    }
                }
                
                # Return the comparative data directly
                tool_to_use = None  # Skip the normal tool use flow
                tool_response = json.dumps(comparison_data)
                update_thought_process(user_id, "Retrieved transportation comparison data for SF to Yosemite", replace=True)
            
            # For SF to Fresno
            elif (origin.lower() in ["san francisco", "sf", "bay area"] and 
                  destination.lower() == "fresno"):
                
                comparison_data = {
                    "comparison": {
                        "driving": {
                            "route": f"Driving from {origin} to {destination}",
                            "distance": "Approximately 190 miles via I-5 S",
                            "duration": "2.5-3 hours",
                            "cost": "$25-35 in gas (estimated)",
                            "advantages": ["No need for airport procedures", 
                                          "Flexible departure time",
                                          "Can bring more luggage"],
                            "disadvantages": ["Driver fatigue", 
                                             "Traffic possible especially near the Bay Area"]
                        },
                        "flying": {
                            "route": f"Flying from SFO to Fresno Yosemite International (FAT)",
                            "details": "Direct flights available on United Airlines",
                            "duration": "Flight time: 1 hour (plus ~2 hours for airport procedures)",
                            "cost": "$120-$220 round trip",
                            "advantages": ["Shorter travel time", 
                                          "Can work or rest during the journey"],
                            "disadvantages": ["Need to arrange ground transportation in Fresno",
                                             "Airport security lines",
                                             "Fixed departure times"]
                        },
                        "recommendation": "For travel between San Francisco and Fresno, flying is faster when accounting for total journey time, while driving offers more flexibility and can be more economical especially for groups. The flight is quick (only 1 hour), but you need to factor in time for airport procedures."
                    }
                }
                
                # Return the comparative data directly
                tool_to_use = None  # Skip the normal tool use flow
                tool_response = json.dumps(comparison_data)
                update_thought_process(user_id, "Retrieved transportation comparison data for SF to Fresno", replace=True)
            
            # For other routes, use Perplexity to get up-to-date info
            else:
                tool_to_use = get_tool_by_name("perplexity_search")
                message = f"Compare {' vs '.join(transport_modes)} from {origin} to {destination} travel time, cost, and convenience in 2025"
                update_thought_process(user_id, f"Using search to compare transportation options from {origin} to {destination}", replace=True)
                
        elif query_type == "poi" or query_type == "recommendations":
            tool_to_use = get_tool_by_name("apify_poi")
            update_thought_process(user_id, "Looking for attractions and points of interest...", replace=True)
            
            # For recommendation queries when we have origin but no destination, use Perplexity instead
            if query_type == "recommendations" and structured_query.get("origin") and not structured_query.get("destination"):
                update_thought_process(user_id, "This looks like a request for destination recommendations. Using Perplexity Search for better results...", replace=True)
                tool_to_use = get_tool_by_name("perplexity_search")
                message = f"Weekend trip destinations from {structured_query.get('origin')} within 3-4 hours by car or short flight"
                logger.info(f"Reformulated as general search: {message}")
            # Use the destination for POI search only when we have a specific destination
            elif structured_query.get("destination"):
                message = structured_query.get("destination")
                logger.info(f"Structured POI query: {message}")
                update_thought_process(user_id, f"Finding attractions and things to do in {message}...", replace=True)
            else:
                # If query doesn't contain a clear destination, switch to Perplexity
                update_thought_process(user_id, "No specific destination found. Using general search for travel recommendations...", replace=True)
                tool_to_use = get_tool_by_name("perplexity_search")
                # Keep the original message, as it's a natural language query
                
        elif query_type == "directions":
            tool_to_use = get_tool_by_name("apify_google_maps")
            update_thought_process(user_id, "Looking for directions and transportation options...", replace=True)
            # Format as directions query
            origin = structured_query.get("origin", "")
            destination = structured_query.get("destination", "")
            if origin and destination:
                message = f"directions from {origin} to {destination}"
                logger.info(f"Structured directions query: {message}")
                update_thought_process(user_id, f"Finding directions from {origin} to {destination}...", replace=True)
                
        # Check for other specific tool needs
        if "translate" in message.lower() or any(lang in message.lower() for lang in ["spanish", "french", "german", "japanese"]):
            tool_to_use = get_tool_by_name("deepl_translate")
            update_thought_process(user_id, "Preparing to translate content...", replace=True)
        
        elif any(term in message.lower() for term in ["book", "reserve", "reservation", "call"]):
            tool_to_use = get_tool_by_name("vapi_reservation")
            update_thought_process(user_id, "Preparing to help you make a reservation...", replace=True)
        
        # Fallback to Perplexity for general queries
        if not tool_to_use and query_type == "general":
            tool_to_use = get_tool_by_name("perplexity_search")
            update_thought_process(user_id, "Searching for general travel information...", replace=True)
            # Use the optimized query if available
            if "structured_query" in structured_query:
                message = structured_query.get("structured_query")
        
        # Step 3: Execute the selected tool
        if tool_to_use:
            logger.info(f"Using tool: {tool_to_use.name}")
            
            # Special handling for reservation tool
            if tool_to_use.name == "vapi_reservation":
                update_thought_process(user_id, "Structuring your reservation details...", replace=True)
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
                        update_thought_process(user_id, f"Making the reservation call with these details: {json_str}", replace=True)
                        tool_response = tool_to_use._run(json_str)
                    else:
                        tool_response = "I couldn't process your reservation request. Could you provide more details about what you'd like to book?"
                except Exception as e:
                    logger.error(f"Error processing reservation: {e}")
                    tool_response = "I encountered an error processing your reservation. Please try again with more details."
            else:
                # For other tools, pass the processed message
                update_thought_process(user_id, f"Using {tool_to_use.name} to get information based on your query...", replace=True)
                start_time = time.time()
                tool_response = tool_to_use._run(message)
                duration = time.time() - start_time
                update_thought_process(
                    user_id, 
                    f"Got response from {tool_to_use.name} in {duration:.1f} seconds. Now analyzing the information...",
                    replace=True
                )
            
            # Check for failed tool runs and try fallback strategies
            if "Error" in tool_response and tool_to_use.name == "apify_google_maps":
                update_thought_process(
                    user_id,
                    "The directions search failed. Switching to a general information search about transportation options...",
                    replace=True
                )
                # Fallback to Perplexity for transportation info
                fallback_tool = get_tool_by_name("perplexity_search")
                fallback_query = f"Transportation options from {structured_query.get('origin', '')} to {structured_query.get('destination', '')} travel guide"
                tool_response = fallback_tool._run(fallback_query)
            
            # Step 4: Process the tool response with LLM to create a conversational reply
            # Include the original query and structured data for context
            update_thought_process(user_id, "Generating a helpful response based on the information gathered...", replace=True)
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
            update_thought_process(user_id, "No specific tool needed. Generating a direct response...", replace=True)
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
        
        # Final thought process update to summarize
        update_thought_process(
            user_id,
            "Response complete! I've saved relevant travel information to help with your trip planning.",
            replace=True
        )
        
        # Instead of using asyncio.create_task, we'll handle this differently
        # since we're running in a thread without an event loop
        try:
            # Schedule the clear thought message for later using threading instead of asyncio
            def clear_thought_later():
                import time
                time.sleep(20)  # Wait 20 seconds before clearing
                if user_id in user_sessions and user_sessions[user_id].get("thought_message_id"):
                    try:
                        if "send_message" in telegram_callbacks:
                            telegram_callbacks["send_message"](
                                user_id,
                                "✓",
                                message_id=user_sessions[user_id]["thought_message_id"],
                                parse_mode="Markdown"
                            )
                    except Exception as e:
                        logger.error(f"Error clearing thought message: {e}")
            
            # Start a thread to clear the thought later
            import threading
            clear_thread = threading.Thread(target=clear_thought_later)
            clear_thread.daemon = True  # This thread won't block program exit
            clear_thread.start()
            
        except Exception as e:
            logger.error(f"Error scheduling thought clearing: {e}")
        
        return final_response
    
    except Exception as e:
        logger.error(f"Error in message processing: {e}", exc_info=True)
        update_thought_process(user_id, f"Sorry, I encountered an error: {str(e)}. Please try again.", replace=True)
        return "I encountered an error while processing your request. Please try again."