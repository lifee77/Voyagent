import os
import logging
import json
from flask import Flask, request, jsonify
from pyngrok import ngrok
from dotenv import load_dotenv
import requests
import threading
import asyncio

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Telegram Bot API token
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN environment variable not set. Please set it in your .env file.")
    TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # Placeholder for error handling
    
TELEGRAM_API = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}'

# Define telegram message functions first before importing agent_runner
def send_message(chat_id, text, parse_mode='HTML'):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': parse_mode
    }
    response = requests.post(url, json=payload)
    if not response.ok:
        logger.error(f"Failed to send message: {response.text}")
    return response.json() if response.ok else None

def send_telegram_message(user_id, text, message_id=None, parse_mode='HTML'):
    """Send or edit a telegram message and return the response.
    This function is registered as a callback for the thought process updates."""
    url = f"{TELEGRAM_API}/{'editMessageText' if message_id else 'sendMessage'}"
    payload = {
        'chat_id': user_id,
        'text': text,
        'parse_mode': parse_mode
    }
    
    # Add message_id for editing existing messages
    if message_id:
        payload['message_id'] = message_id
    
    try:
        response = requests.post(url, json=payload)
        if not response.ok:
            logger.error(f"Failed to {'edit' if message_id else 'send'} message: {response.text}")
            # If editing fails (e.g., no changes in content), try sending a new message
            if message_id:
                return send_telegram_message(user_id, text, None, parse_mode)
        return response.json() if response.ok else None
    except Exception as e:
        logger.error(f"Error in send_telegram_message: {e}")
        return None

def send_chat_action(chat_id, action):
    """Send chat action like typing, upload_photo, etc."""
    url = f"{TELEGRAM_API}/sendChatAction"
    payload = {
        'chat_id': chat_id,
        'action': action
    }
    response = requests.post(url, json=payload)
    if not response.ok:
        logger.error(f"Failed to send chat action: {response.text}")
    return response

# Now import agent handler after defining the telegram functions
from Voyagent.agent_runner import process_message, register_telegram_callback

# Register the Telegram callback function for sending thought process updates
register_telegram_callback(send_telegram_message)

@app.route('/', methods=['GET'])
def index():
    return "Telegram Trip Assistant Bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    logger.info(f"Received update: {json.dumps(data, indent=2)}")
    
    # Check if this is a message or command
    if 'message' in data:
        chat_id = data['message']['chat']['id']
        
        # Send typing action to let user know we're processing
        send_chat_action(chat_id, 'typing')
        
        # Check if it's a command
        if 'text' in data['message']:
            message_text = data['message']['text']
            user_info = {
                'id': data['message']['from']['id'],
                'first_name': data['message']['from'].get('first_name', ''),
                'username': data['message']['from'].get('username', '')
            }
            
            if message_text.startswith('/start'):
                send_message(chat_id, "Welcome to Trip-Assistant! 🌍✈️\n\nI can help you plan your trips. Ask me about flights, things to do, or places to visit. When you're ready for a summary of your trip, just type /summary.")
                return jsonify({"status": "ok"})
            
            elif message_text.startswith('/summary'):
                # Process summary request in a separate thread
                threading.Thread(target=handle_summary_request, args=(chat_id, user_info)).start()
                return jsonify({"status": "ok"})
            
            elif message_text.startswith('/call'):
                # Process call request in a separate thread
                threading.Thread(target=handle_call_request, args=(chat_id, message_text, user_info)).start()
                return jsonify({"status": "ok"})
            
            else:
                # Process regular message in a separate thread
                threading.Thread(target=handle_message, args=(chat_id, message_text, user_info)).start()
                return jsonify({"status": "ok"})
    
    return jsonify({"status": "ok"})

@app.route('/setup_webhook', methods=['GET'])
def setup_webhook_route():
    """Setup webhook manually with the provided ngrok URL"""
    ngrok_url = request.args.get('ngrok_url')
    
    if not ngrok_url:
        return "Please provide a ngrok_url parameter with your ngrok URL", 400
    
    result = setup_webhook(ngrok_url)
    return jsonify({"status": "Webhook setup attempted", "result": result})

@app.route('/check_webhook', methods=['GET'])
def check_webhook():
    """Check the current webhook status"""
    url = f"{TELEGRAM_API}/getWebhookInfo"
    response = requests.get(url)
    return jsonify(response.json())

def handle_message(chat_id, message_text, user_info):
    try:
        # Process message with agent
        response = process_message(message_text, user_info)
        send_message(chat_id, response, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        send_message(chat_id, "I encountered an error while processing your request. Please try again.", parse_mode='HTML')

def handle_summary_request(chat_id, user_info):
    try:
        # Get summary from agent
        from Voyagent.summary_generator import generate_summary
        summary = generate_summary(user_info['id'])
        send_message(chat_id, summary)
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        send_message(chat_id, "I couldn't generate your trip summary. Please try asking a few questions about your destination first.")

def handle_call_request(chat_id, message_text, user_info):
    """Handle a call request from the user."""
    try:
        # Extract phone number from the command
        parts = message_text.split()
        if len(parts) < 2:
            send_message(chat_id, "Please provide a phone number to call. Example: /call +14158667151")
            return
        
        phone_number = parts[1]
        
        # Get the Vapi call tool
        from Voyagent.tools.vapi import VapiCallTool
        call_tool = VapiCallTool()
        
        # Make the call
        response = call_tool._run(phone_number)
        send_message(chat_id, response)
        
    except Exception as e:
        logger.error(f"Error handling call request: {e}")
        send_message(chat_id, "I encountered an error while processing your call request. Please try again.")

def setup_webhook(ngrok_url):
    """Set up the Telegram webhook"""
    webhook_url = f"{ngrok_url}/webhook"
    url = f"{TELEGRAM_API}/setWebhook"
    payload = {
        "url": webhook_url,
        "allowed_updates": ["message"]
    }
    
    # Use POST instead of GET for setting webhook
    response = requests.post(url, json=payload)
    logger.info(f"Webhook set: {response.json()}")
    return response.json()

# Set up asyncio event loop for the main thread
def setup_asyncio_event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

if __name__ == '__main__':
    # Set up asyncio event loop for the main thread
    setup_asyncio_event_loop()
    
    # Get port from environment or default to 8080 (instead of 5000 to avoid AirPlay conflicts on macOS)
    port = int(os.getenv('PORT', 8080))
    
    # Start ngrok tunnel
    try:
        public_url = ngrok.connect(port).public_url
        logger.info(f"Public URL: {public_url}")
        
        # Setup webhook
        webhook_response = setup_webhook(public_url)
        logger.info(f"Webhook response: {webhook_response}")
    except Exception as e:
        logger.error(f"Error setting up ngrok or webhook: {e}")
        logger.info("You can manually set up the webhook using /setup_webhook route")
    
    # Start Flask app
    app.run(host='0.0.0.0', port=port)