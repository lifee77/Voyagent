#!/usr/bin/env python3
import os
import requests
import json
import time

# Get API key from environment variable or ask for it
api_key = os.environ.get("VAPI_API_KEY")
if not api_key:
    print("Please provide your Vapi API key:")
    api_key = input().strip()

# Get phone number ID from environment or ask for it
phone_number_id = os.environ.get("VAPI_PHONE_NUMBER_ID")
if not phone_number_id:
    print("Please provide your Vapi Phone Number ID (from dashboard):")
    phone_number_id = input().strip()

# Phone number to call
customer_number = "+14158667151"  # Your recipient's number

# Create headers with Authorization token
headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json',
}

# Create the data payload based on the correct API structure
data = {
    'assistant': {
        "firstMessage": "Hello! This is a test call from Voyagent.",
        "model": {
            "provider": "google",
            "model": "gemini-2.0-flash",
            "messages": [
                {
                    "role": "system",
                    "content": "You are Voyagent, an AI assistant making a test call. Be professional, friendly, and conversational. Introduce yourself and explain this is a test call. Keep it brief and thank them for their time."
                }
            ]
        },
        "voice": "eva-rime-ai"  # Using a standard voice
    },
    'phoneNumberId': phone_number_id,
    'customer': {
        'number': customer_number,
    },
}

# API endpoint - note this is different from what we tried before
url = 'https://api.vapi.ai/call/phone'

print(f"Making API request to {url}")
print(f"Using phone number ID: {phone_number_id}")
print(f"Calling customer number: {customer_number}")
print(f"\nPayload structure: {json.dumps(data, indent=2)}")

try:
    # Make the POST request to initiate the call
    print("\nSending request...")
    response = requests.post(url, headers=headers, json=data)
    
    # Print the response details
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Check if call was created successfully (201 Created status)
    if response.status_code == 201:
        response_data = response.json()
        print("\nCall created successfully!")
        print("Full response data:", json.dumps(response_data, indent=2))
        
        # Try to get the call ID
        call_id = response_data.get("id", "")
        
        if call_id:
            print(f"Call ID: {call_id}")
            
            # Monitor call status (this part is optional)
            print("\nMonitoring call status...")
            status_url = f"https://api.vapi.ai/call/{call_id}"
            
            # Check status for up to 3 minutes
            max_wait_time = 180  # seconds
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                status_response = requests.get(status_url, headers=headers)
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get("status", "unknown")
                    print(f"Current status: {status}")
                    
                    if status in ["completed", "failed", "expired"]:
                        # Call is finished
                        if status == "completed" and "transcript" in status_data:
                            print("\nCall Transcript:")
                            print(status_data["transcript"])
                        break
                else:
                    print(f"Failed to get status: {status_response.status_code}")
                
                # Wait before checking again
                time.sleep(10)
        else:
            print("No call ID found in response")
    else:
        print("\nFailed to create call")
        
except Exception as e:
    print(f"\nError: {str(e)}") 