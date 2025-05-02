import os
import json
import logging
import time
from dotenv import load_dotenv
from langchain.tools import BaseTool
from rime.client import RimeClient, CallTaskSpec
from rime.exceptions import ApiError, CallTaskError

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class RimeReservationTool(BaseTool):
    name = "rime_reservation"
    description = """
    Uses Rime to make phone calls to travel agents, restaurants, hotels, or other services
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
        """Make a reservation call using Rime."""
        logger.info(f"TOOL: rime_reservation - Query: {query}")
        
        api_key = os.getenv("RIME_API_KEY")
        if not api_key:
            logger.error("Rime API key not found")
            return "Error: Rime API key not configured"
        
        try:
            # Parse the input query as JSON
            params = json.loads(query)
            
            # Validate required fields
            required_fields = ["service_type", "service_name", "phone_number", "user_name"]
            for field in required_fields:
                if field not in params:
                    return f"Error: Missing required field '{field}'"
            
            # Initialize Rime client
            client = RimeClient(api_key=api_key)
            
            # Create the call instruction based on service type
            call_instruction = self._generate_call_instruction(params)
            
            # In a real implementation, make the actual Rime call
            # Example Rime call:
            # task = client.create_call_task(
            #     CallTaskSpec(
            #         phone_number=params["phone_number"],
            #         call_script=call_instruction,
            #         caller_id=os.getenv("RIME_CALLER_ID", ""),  # Optional caller ID
            #         webhook_url="https://your-webhook-endpoint.com",  # Optional webhook
            #         agent_mode="voice"  # Or "interactive"
            #     )
            # )
            
            # Wait for call completion
            # status = client.get_call_task(task.task_id)
            # while status.state not in ["completed", "failed", "expired"]:
            #     time.sleep(10)
            #     status = client.get_call_task(task.task_id)
            
            # Call summary
            # summary = f"Call completed with status: {status.state}"
            # if status.state == "completed":
            #     summary += f"\nReservation outcome: {status.outcome}"
            # else:
            #     summary += f"\nReason: {status.failure_reason}"
            
            # For demo purposes, return mock response
            mock_response = self._get_mock_reservation_response(params)
            return mock_response
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON format in query")
            return "Error: The reservation details must be provided in valid JSON format"
        except Exception as e:
            logger.error(f"Error making Rime call: {e}")
            return f"Error making reservation: {str(e)}"
    
    def _generate_call_instruction(self, params):
        """Generate appropriate call instructions based on service type."""
        service_type = params["service_type"]
        service_name = params["service_name"]
        user_name = params["user_name"]
        reservation_details = params.get("reservation_details", {})
        
        # Base introduction
        introduction = f"Hello, I'm calling on behalf of {user_name} to make a reservation."
        
        if service_type == "restaurant":
            date = reservation_details.get("date", "today")
            time = reservation_details.get("time", "7:00 PM")
            num_people = reservation_details.get("num_people", 2)
            special_requests = reservation_details.get("special_requests", "")
            
            script = f"{introduction}\n\n"
            script += f"I'd like to make a reservation at {service_name} for {num_people} people on {date} at {time}.\n"
            if special_requests:
                script += f"We have the following special requests: {special_requests}\n"
            script += f"\nThe reservation should be under the name: {user_name}\n"
            script += "\nPlease confirm the reservation details and any deposit requirements."
            
        elif service_type == "hotel":
            check_in = reservation_details.get("date", "")
            duration = reservation_details.get("duration", "")
            num_people = reservation_details.get("num_people", 1)
            special_requests = reservation_details.get("special_requests", "")
            
            script = f"{introduction}\n\n"
            script += f"I'd like to book a room at {service_name} for {num_people} guest(s).\n"
            script += f"The check-in date would be {check_in}"
            if duration:
                script += f" for a duration of {duration}.\n"
            else:
                script += ".\n"
            if special_requests:
                script += f"We have the following special requests: {special_requests}\n"
            script += f"\nThe reservation should be under the name: {user_name}\n"
            script += "\nPlease confirm availability, pricing, and booking details."
            
        elif service_type == "attraction":
            date = reservation_details.get("date", "")
            time = reservation_details.get("time", "")
            num_people = reservation_details.get("num_people", 1)
            
            script = f"{introduction}\n\n"
            script += f"I'd like to reserve tickets for {service_name} for {num_people} person(s).\n"
            if date:
                script += f"The visit date would be {date}"
                if time:
                    script += f" at around {time}.\n"
                else:
                    script += ".\n"
            script += f"\nThe reservation should be under the name: {user_name}\n"
            script += "\nPlease confirm availability, pricing, and any booking requirements."
            
        elif service_type == "travel_agent":
            script = f"{introduction}\n\n"
            script += f"I'm interested in learning more about travel packages or services from {service_name}.\n"
            script += "Specifically, I'm looking for information about:\n"
            
            if "destination" in reservation_details:
                script += f"- Travel to {reservation_details['destination']}\n"
            if "date" in reservation_details:
                script += f"- For the date(s): {reservation_details['date']}\n"
            if "num_people" in reservation_details:
                script += f"- For {reservation_details['num_people']} person(s)\n"
            if "special_requests" in reservation_details:
                script += f"- Additional details: {reservation_details['special_requests']}\n"
                
            script += f"\nMy name is {user_name} and I'm exploring options for an upcoming trip.\n"
            script += "\nPlease provide information about available packages, pricing, and booking procedures."
            
        else:
            script = f"{introduction}\n\n"
            script += f"I'd like to make an inquiry about services at {service_name}.\n"
            script += f"I'm calling on behalf of {user_name}.\n"
            script += "\nCould you please provide information about availability and booking procedures?"
            
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
            Reservation Successfully Made!
            
            Restaurant: {service_name}
            Date: {date}
            Time: {time}
            Number of people: {num_people}
            Reservation name: {user_name}
            
            Confirmation #: RES-{hash(service_name + user_name)%10000:04d}
            
            Additional notes: Please arrive 15 minutes before your reservation time.
            The restaurant requests a call back if your party size changes.
            """
            
        elif service_type == "hotel":
            details = params.get("reservation_details", {})
            check_in = details.get("date", "May 10, 2025")
            duration = details.get("duration", "3 nights")
            
            return f"""
            Hotel Booking Confirmed!
            
            Hotel: {service_name}
            Check-in date: {check_in}
            Duration: {duration}
            Guest name: {user_name}
            
            Confirmation #: HTL-{hash(service_name + user_name)%10000:04d}
            
            Additional notes: Check-in time is after 3:00 PM. Please bring ID and
            the credit card used for booking. Breakfast is included in your stay.
            """
            
        elif service_type == "attraction":
            details = params.get("reservation_details", {})
            date = details.get("date", "May 12, 2025")
            num_people = details.get("num_people", 2)
            
            return f"""
            Attraction Tickets Reserved!
            
            Attraction: {service_name}
            Date: {date}
            Number of tickets: {num_people}
            Reservation name: {user_name}
            
            Confirmation #: ATT-{hash(service_name + user_name)%10000:04d}
            
            Additional notes: Please arrive 30 minutes before your scheduled time
            to collect your tickets. Bring ID and the credit card used for purchase.
            """
            
        elif service_type == "travel_agent":
            details = params.get("reservation_details", {})
            destination = details.get("destination", "your destination")
            
            return f"""
            Travel Agent Inquiry Complete!
            
            Agency: {service_name}
            Destination: {destination}
            Inquiry name: {user_name}
            
            The travel agent has provided information about available packages and
            will send detailed options to your email within 24 hours.
            
            Reference #: TRV-{hash(service_name + user_name)%10000:04d}
            
            Additional notes: The agent recommended booking at least 45 days in advance
            to secure the best rates and availability.
            """
            
        else:
            return f"""
            Service Inquiry Complete!
            
            Service: {service_name}
            Inquiry name: {user_name}
            
            Your inquiry has been processed. The service has confirmed availability
            and will hold your spot for 24 hours.
            
            Reference #: SVC-{hash(service_name + user_name)%10000:04d}
            
            Please call back to finalize your booking with payment details.
            """