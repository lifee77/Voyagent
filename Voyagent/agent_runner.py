import os
import json
import logging
from dotenv import load_dotenv
from langchain.agents import AgentExecutor
# Fix import paths for current langchain version
from langchain.agents.format_scratchpad.openai_functions import format_to_openai_function_messages
from langchain.agents.output_parsers.openai_functions import OpenAIFunctionsAgentOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.tools.render import format_tool_to_openai_function
from langchain.schema import SystemMessage, HumanMessage

# Import tool implementations
from Voyagent.tools.perplexity import PerplexitySearchTool
from Voyagent.tools.apify import ApifyFlightTool, ApifyPOITool
from Voyagent.tools.deepl import DeepLTranslateTool
from Voyagent.tools.vapi import VapiReservationTool  # Changed from RimeReservationTool to VapiReservationTool
from Voyagent.cache_manager import save_to_cache, get_from_cache

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Initialize LLM
llm = ChatOpenAI(
    temperature=0,
    model="gpt-4-turbo",
    api_key=os.getenv("OPENAI_API_KEY")
)

# Initialize tools
tools = [
    PerplexitySearchTool(),
    ApifyFlightTool(),
    ApifyPOITool(),
    DeepLTranslateTool(),
    VapiReservationTool()  # Changed from RimeReservationTool to VapiReservationTool
]

# Format tools for OpenAI functions
tool_functions = [format_tool_to_openai_function(t) for t in tools]

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

# Create prompt template
prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content=SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="chat_history"),
    HumanMessage(content="{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad")
])

# Set up the agent
agent = (
    {
        "input": lambda x: x["input"],
        "chat_history": lambda x: x.get("chat_history", []),
        "agent_scratchpad": lambda x: format_to_openai_function_messages(
            x["intermediate_steps"]
        ),
    }
    | prompt
    | llm.bind(functions=tool_functions)
    | OpenAIFunctionsAgentOutputParser()
)

# Create agent executor
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=4
)

# Dictionary to store user chat history and context
user_sessions = {}

def process_message(message, user_info):
    """Process a message using the agent and store results in cache"""
    user_id = user_info['id']
    
    # Initialize user session if it doesn't exist
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "chat_history": [],
            "trip_info": {}
        }
    
    # Execute agent
    logger.info(f"Processing message from User {user_id}: {message}")
    try:
        result = agent_executor.invoke({
            "input": message,
            "chat_history": user_sessions[user_id]["chat_history"]
        })
        
        # Update chat history
        user_sessions[user_id]["chat_history"].append(HumanMessage(content=message))
        user_sessions[user_id]["chat_history"].append(SystemMessage(content=result["output"]))
        
        # Extract and cache important travel information
        save_to_cache(user_id, message, result)
        
        return result["output"]
    
    except Exception as e:
        logger.error(f"Error in agent execution: {e}")
        return "I encountered an error while processing your request. Please try again."