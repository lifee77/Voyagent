import os
import json
import logging
from dotenv import load_dotenv
# Import the correct modules
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

# Import tool implementations
from Voyagent.tools.perplexity import PerplexitySearchTool
from Voyagent.tools.apify import ApifyFlightTool, ApifyPOITool
from Voyagent.tools.deepl import DeepLTranslateTool
from Voyagent.tools.vapi import VapiReservationTool
from Voyagent.cache_manager import save_to_cache, get_from_cache

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# System prompt
SYSTEM_PROMPT = """You are a helpful Trip Assistant bot that helps users plan their travel.
You have access to these tools:

1. Perplexity Search - Use this to search for general travel information, current events, or anything that needs up-to-date information
2. Apify Flight Finder - Use this to find flight information when users ask about travel between cities
3. Apify Points of Interest - Use this to find attractions, restaurants, and activities in a destination
4. DeepL Translate - Use this to translate text if the user asks for information in a different language
5. Vapi Reservation - Use this to make actual phone calls to book restaurants, hotels, attractions, or contact travel agents when the user explicitly requests to make a reservation or booking

When the user asks a travel-related question:
- If they ask about flights, use the Apify Flight Finder tool
- If they ask about things to do, places to visit, or attractions, use the Apify Points of Interest tool
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

# Initialize LLM with OpenAI API key
llm = ChatOpenAI(
    model="gpt-4-turbo",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)

# Initialize tools
tools = [
    PerplexitySearchTool(),
    ApifyFlightTool(),
    ApifyPOITool(),
    DeepLTranslateTool(),
    VapiReservationTool()
]

# Dictionary to store user chat history and context
user_sessions = {}

def process_message(message, user_info):
    """Process a message using direct tool calling and LLM for response generation"""
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
        # Step 1: Check if the message needs a specialized tool
        tool_to_use = None
        
        # Check for flight queries
        if any(keyword in message.lower() for keyword in ['flight', 'fly', 'ticket', 'travel to', 'from']):
            tool_to_use = next((tool for tool in tools if tool.name == "apify_flight"), None)
        
        # Check for attraction queries
        elif any(keyword in message.lower() for keyword in ['attraction', 'visit', 'thing to do', 'restaurant', 'activity']):
            tool_to_use = next((tool for tool in tools if tool.name == "apify_poi"), None)
        
        # Check for translation requests
        elif any(keyword in message.lower() for keyword in ['translate', 'language', 'spanish', 'french', 'german']):
            tool_to_use = next((tool for tool in tools if tool.name == "deepl_translate"), None)
            
        # Check for reservation requests
        elif any(keyword in message.lower() for keyword in ['book', 'reserve', 'reservation', 'call']):
            tool_to_use = next((tool for tool in tools if tool.name == "vapi_reservation"), None)
        
        # General information queries default to Perplexity
        else:
            tool_to_use = next((tool for tool in tools if tool.name == "perplexity_search"), None)
        
        # Step 2: Use the appropriate tool or fallback to direct LLM
        if tool_to_use:
            logger.info(f"Using tool: {tool_to_use.name}")
            
            # For reservation tool, we need LLM help to structure the input
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
                # For other tools, pass the message directly
                tool_response = tool_to_use._run(message)
            
            # Now use LLM to create a good response based on the tool output
            response_prompt = f"""Based on this user question: "{message}"
            
            And this tool response:
            "{tool_response}"
            
            Create a helpful, conversational response. Include the most relevant information from the tool output but make it sound natural and conversational. If the tool returned structured data, format it in a readable way."""
            
            response_messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=response_prompt)
            ]
            
            final_response = llm.invoke(response_messages).content
            
            # Create a structured result for cache_manager
            structured_result = {
                "output": final_response,
                "intermediate_steps": [
                    [{"tool": tool_to_use.name, "tool_input": message}, tool_response]
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
            
            # Add the current user message
            messages.append(HumanMessage(content=message))
            
            # Get response from LLM
            final_response = llm.invoke(messages).content
            
            structured_result = {
                "output": final_response,
                "intermediate_steps": []
            }
        
        # Update chat history
        user_sessions[user_id]["chat_history"].append(HumanMessage(content=message))
        user_sessions[user_id]["chat_history"].append(AIMessage(content=final_response))
        
        # Extract and cache important travel information
        save_to_cache(user_id, message, structured_result)
        
        return final_response
    
    except Exception as e:
        logger.error(f"Error in message processing: {e}")
        return "I encountered an error while processing your request. Please try again."