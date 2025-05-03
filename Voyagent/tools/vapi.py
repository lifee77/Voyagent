import os
import json
import logging
import time
import requests
from dotenv import load_dotenv
from langchain.tools import BaseTool
from typing import Dict, Any

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class VapiReservationTool(BaseTool):
    name = "vapi_reservation"
    description = """
    Uses Vapi.ai to make phone calls to travel agents, restaurants, hotels, or other services
    to make reservations or book services for the trip. This is useful when you need to:
    1. Make restaurant reservations
    2. Book hotel rooms
    3. Reserve tickets for attractions
    4. Confirm tour availability
    5. Check with travel agencies about package deals
    
    Important: Only use this when the user explicitly requests to make a reservation or booking.
    
    Input should be in JSON format with these fields:
    {
        "service_type": "restaurant|hotel|attraction|travel_agent",
        "service_name": "Name of the business",
        "phone_number": "Phone number with country code",
        "reservation_details": {
            "date": "YYYY-MM-DD",
            "time": "HH:MM" (for restaurants),
            "num_people": Number of people,
            "special_requests": "Any special requests or notes",
            "duration": "Length of stay for hotels",
            "confirmation_email": "Email for confirmation"
        },
        "user_name": "Name for the reservation"
    }
    """
    
    def _run(self, query: str) -> str:
        """Make a reservation call using Vapi.ai."""
        logger.info(f"TOOL: vapi_reservation - Query: {query}")
        
        api_key = os.getenv("VAPI_API_KEY")
        if not api_key:
            logger.error("Vapi API key not found")
            return "Error: Vapi API key not configured"
        
        try:
            # Parse the input query as JSON
            params = json.loads(query)
            
            # Validate required fields
            required_fields = ["service_type", "service_name", "phone_number", "user_name"]
            for field in required_fields:
                if field not in params:
                    return f"Error: Missing required field '{field}'"
            
            # Create the call instruction based on service type
            call_instruction = self._generate_call_instruction(params)
            
            # Prepare the request to Vapi.ai MCP server
            url = "https://mcp.vapi.ai/call"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "phoneNumber": params["phone_number"],
                "assistant": {
                    "instruction": call_instruction,
                    "name": "Voyagent",
                    "model": "gpt-4"
                },
                "recordingEnabled": True,
                "webhookUrl": os.getenv("VAPI_WEBHOOK_URL", ""),
                "firstMessage": "Hello, this is Voyagent calling on behalf of a client. I'd like to make a reservation."
            }
            
            # In a real implementation, make the actual Vapi call
            # Example Vapi call:
            # response = requests.post(url, headers=headers, json=payload)
            # response.raise_for_status()
            # call_id = response.json().get("callId")
            
            # Wait for call completion or timeout
            # For demo purposes, mock the call and return sample result
            logger.info("Would make Vapi.ai call with the following payload:")
            logger.info(json.dumps(payload, indent=2))
            
            # For demo purposes, return mock response
            mock_response = self._get_mock_reservation_response(params)
            return mock_response
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON format in query")
            return "Error: The reservation details must be provided in valid JSON format"
        except Exception as e:
            logger.error(f"Error making Vapi call: {e}")
            return f"Error making reservation: {str(e)}"
    
    def _generate_call_instruction(self, params):
        """Generate appropriate call instructions based on service type."""
        service_type = params["service_type"]
        service_name = params["service_name"]
        user_name = params["user_name"]
        reservation_details = params.get("reservation_details", {})
        
        # Base introduction
        introduction = f"You are Voyagent, an AI assistant calling to make a reservation on behalf of {user_name}. Be professional, direct, and friendly. Speak naturally and get the task done efficiently. Make realistic responses to questions. If you can't make a reservation, apologize politely and explain why."
        
        if service_type == "restaurant":
            date = reservation_details.get("date", "today")
            time = reservation_details.get("time", "7:00 PM")
            num_people = reservation_details.get("num_people", 2)
            special_requests = reservation_details.get("special_requests", "")
            
            script = f"{introduction}\n\n"
            script += f"Your goal is to make a reservation at {service_name} for {num_people} people on {date} at {time}.\n"
            if special_requests:
                script += f"Mention these special requests: {special_requests}\n"
            script += f"\nThe reservation should be under the name: {user_name}\n"
            script += "\nIf they ask for a callback number, explain that you're calling on behalf of a client and cannot provide a direct number, but they can reach out to the customer directly."
            script += "\nAfter making the reservation, confirm the details, including date, time, party size, and ask if there's any deposit required."
            
        elif service_type == "hotel":
            check_in = reservation_details.get("date", "")
            duration = reservation_details.get("duration", "")
            num_people = reservation_details.get("num_people", 1)
            special_requests = reservation_details.get("special_requests", "")
            
            script = f"{introduction}\n\n"
            script += f"Your goal is to book a room at {service_name} for {num_people} guest(s).\n"
            script += f"The check-in date would be {check_in}"
            if duration:
                script += f" for a duration of {duration}.\n"
            else:
                script += ".\n"
            if special_requests:
                script += f"Mention these special requests: {special_requests}\n"
            script += f"\nThe reservation should be under the name: {user_name}\n"
            script += "\nConfirm availability, pricing details, and any booking requirements such as deposit or ID required at check-in."
            
        elif service_type == "attraction":
            date = reservation_details.get("date", "")
            time = reservation_details.get("time", "")
            num_people = reservation_details.get("num_people", 1)
            
            script = f"{introduction}\n\n"
            script += f"Your goal is to reserve tickets for {service_name} for {num_people} person(s).\n"
            if date:
                script += f"The visit date would be {date}"
                if time:
                    script += f" at around {time}.\n"
                else:
                    script += ".\n"
            script += f"\nThe reservation should be under the name: {user_name}\n"
            script += "\nConfirm availability, pricing, any booking requirements, and what the tickets include."
            
        elif service_type == "travel_agent":
            script = f"{introduction}\n\n"
            script += f"Your goal is to gather information about travel packages or services from {service_name}.\n"
            script += "Specifically, ask about:\n"
            
            if "destination" in reservation_details:
                script += f"- Travel to {reservation_details['destination']}\n"
            if "date" in reservation_details:
                script += f"- For the date(s): {reservation_details['date']}\n"
            if "num_people" in reservation_details:
                script += f"- For {reservation_details['num_people']} person(s)\n"
            if "special_requests" in reservation_details:
                script += f"- With these requirements: {reservation_details['special_requests']}\n"
                
            script += f"\nMention that you're calling on behalf of {user_name} who is exploring options for an upcoming trip.\n"
            script += "\nIf they can provide package information, ask about pricing, availability, and booking procedures."
            
        else:
            script = f"{introduction}\n\n"
            script += f"Your goal is to make an inquiry about services at {service_name}.\n"
            script += f"You're calling on behalf of {user_name}.\n"
            script += "\nFind out about availability and booking procedures for their services."
            
        return script
    
    def _get_mock_reservation_response(self, params):
        """Generate mock reservation response for demo purposes."""
        service_type = params["service_type"]
        service_name = params["service_name"]
        user_name = params["user_name"]
        
        if service_type == "restaurant":
            details = params.get("reservation_details", {})
            date = details.get("date", "May 5, 2025")
            time = details.get("time", "7:00 PM")
            num_people = details.get("num_people", 2)
            
            return f"""
            Call completed! Reservation successfully made.
            
            Restaurant: {service_name}
            Date: {date}
            Time: {time}
            Number of people: {num_people}
            Reservation name: {user_name}
            
            Confirmation #: RES-{hash(service_name + user_name)%10000:04d}
            
            Call summary: The restaurant confirmed your reservation and requested you arrive 15 minutes before your reservation time. They noted that they may hold the table for only 15 minutes if your party is late.
            """
            
        elif service_type == "hotel":
            details = params.get("reservation_details", {})
            check_in = details.get("date", "May 10, 2025")
            duration = details.get("duration", "3 nights")
            
            return f"""
            Call completed! Hotel booking confirmed.
            
            Hotel: {service_name}
            Check-in date: {check_in}
            Duration: {duration}
            Guest name: {user_name}
            
            Confirmation #: HTL-{hash(service_name + user_name)%10000:04d}
            
            Call summary: The hotel confirmed your reservation and provided the following information: Check-in time is after 3:00 PM. They require a credit card to hold the reservation, which will be collected at check-in. Breakfast is included in your stay.
            """
            
        elif service_type == "attraction":
            details = params.get("reservation_details", {})
            date = details.get("date", "May 12, 2025")
            num_people = details.get("num_people", 2)
            
            return f"""
            Call completed! Attraction tickets reserved.
            
            Attraction: {service_name}
            Date: {date}
            Number of tickets: {num_people}
            Reservation name: {user_name}
            
            Confirmation #: ATT-{hash(service_name + user_name)%10000:04d}
            
            Call summary: The attraction has reserved your tickets. They advised arriving 30 minutes before your scheduled time to collect your tickets from the will-call window. Please bring ID and the credit card used for purchase.
            """
            
        elif service_type == "travel_agent":
            details = params.get("reservation_details", {})
            destination = details.get("destination", "your destination")
            
            return f"""
            Call completed! Travel inquiry successful.
            
            Agency: {service_name}
            Destination: {destination}
            Inquiry name: {user_name}
            
            Reference #: TRV-{hash(service_name + user_name)%10000:04d}
            
            Call summary: The travel agent provided information about available packages for {destination}. They will email detailed options to you within 24 hours. They recommended booking at least 45 days in advance to secure the best rates and availability.
            """
            
        else:
            return f"""
            Call completed! Service inquiry successful.
            
            Service: {service_name}
            Inquiry name: {user_name}
            
            Reference #: SVC-{hash(service_name + user_name)%10000:04d}
            
            Call summary: The service has confirmed availability and will hold a spot for you for 24 hours. They request that you call back directly to finalize your booking with payment details.
            """

class VapiCallTool(BaseTool):
    name = "vapi_call"
    description = """
    Makes a phone call using the Vapi API.
    Input should be a phone number to call, optionally with a message to deliver.
    Example: "+14158667151" or "call +14158667151 with message 'Hello, this is a test call'"
    """
    
    def _run(self, query: str) -> str:
        """Make a phone call using Vapi."""
        logger.info(f"TOOL: vapi_call - Query: {query}")
        
        # Get API credentials
        api_key = os.getenv("VAPI_API_KEY")
        phone_number_id = os.getenv("VAPI_PHONE_NUMBER_ID")
        
        if not api_key or not phone_number_id:
            logger.error("Vapi API credentials not found")
            return "Error: Vapi API credentials not configured"
        
        # Extract phone number and message from query
        phone_number = None
        message = "Hello! This is a call from Voyagent."
        
        # Try to extract phone number and message
        if "with message" in query:
            parts = query.split("with message")
            phone_number = parts[0].strip()
            message = parts[1].strip().strip("'\"")
        else:
            phone_number = query.strip()
        
        # Validate phone number format
        if not phone_number.startswith("+"):
            phone_number = "+" + phone_number
        
        # Create headers with Authorization token
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }
        
        # Create the data payload
        data = {
            'assistant': {
                "firstMessage": message,
                "model": {
                    "provider": "google",
                    "model": "gemini-2.0-flash",
                    "messages": [
                        {
                            "role": "system",
                            "content": """You are Voyagent, an AI assistant making a call to make a reservation. 
Your primary goal is to make a reservation for the customer. Be professional, friendly, and direct.
Follow these steps:
1. Introduce yourself as Voyagent
2. State that you're calling to make a reservation
3. Ask for availability and make the reservation
4. Confirm all details (date, time, number of people, special requests)
5. Get a confirmation number if available
6. Thank them for their time

If they ask about services or pricing, politely redirect the conversation back to making the reservation.
Keep the conversation focused on completing the reservation."""
                        }
                    ]
                },
                "voice": "eva-rime-ai"  # Using a standard voice
            },
            'phoneNumberId': phone_number_id,
            'customer': {
                'number': phone_number,
            },
        }
        
        # API endpoint
        url = 'https://api.vapi.ai/call/phone'
        
        try:
            # Make the POST request to initiate the call
            logger.info(f"Making API request to {url}")
            response = requests.post(url, headers=headers, json=data)
            
            # Check if call was created successfully
            if response.status_code == 201:
                response_data = response.json()
                call_id = response_data.get("id", "")
                
                if call_id:
                    logger.info(f"Call created successfully with ID: {call_id}")
                    
                    # Monitor call status
                    status_url = f"https://api.vapi.ai/call/{call_id}"
                    max_wait_time = 180  # 3 minutes
                    start_time = time.time()
                    
                    while time.time() - start_time < max_wait_time:
                        status_response = requests.get(status_url, headers=headers)
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            status = status_data.get("status", "unknown")
                            
                            if status in ["completed", "failed", "expired"]:
                                if status == "completed" and "transcript" in status_data:
                                    # Format the transcript for better readability
                                    transcript = status_data["transcript"]
                                    formatted_transcript = "📞 Call Transcript:\n\n"
                                    
                                    # Split transcript into lines and format each line
                                    for line in transcript.split('\n'):
                                        if line.strip():
                                            # Add speaker labels and formatting
                                            if line.startswith('Assistant:'):
                                                formatted_transcript += f"🤖 {line}\n"
                                            elif line.startswith('Customer:'):
                                                formatted_transcript += f"👤 {line}\n"
                                            else:
                                                formatted_transcript += f"{line}\n"
                                    
                                    return formatted_transcript
                                else:
                                    return f"Call {status}. No transcript available."
                            break
                        
                        time.sleep(10)
                    
                    return "Call initiated successfully. Status monitoring timed out."
                else:
                    return "Error: No call ID received from Vapi API"
            else:
                logger.error(f"Failed to create call: {response.text}")
                return f"Error: Failed to create call. Status code: {response.status_code}"
                
        except Exception as e:
            logger.error(f"Error making Vapi call: {e}")
            return f"Error making call: {str(e)}"