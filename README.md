# Telegram Trip-Assistant Bot

A Telegram bot that helps users plan their trips by providing flight information, points of interest, and travel recommendations. The bot uses LangChain's agent framework to integrate with multiple sponsor APIs:

1. **Perplexity Sonar API** - For real-time travel information and general queries
2. **Apify Actors** - For structured flight and attraction data
3. **DeepL** - For multi-language translation support
4. **Rime** - For making actual phone calls to book restaurants, hotels, and attractions

## Features

- Search for flights between cities using Apify
- Find attractions, restaurants, and activities at destinations
- Get real-time information about travel destinations using Perplexity
- Translate information into multiple languages with DeepL
- Make real reservations via phone calls using Rime's AI voice agents
- Create trip summaries with the `/summary` command

## Setup Instructions

### 1. Prerequisites

- Python 3.8+
- A Telegram account
- API keys for Perplexity, Apify, DeepL, and Rime
- An OpenAI API key for LangChain

### 2. Get a Telegram Bot Token

1. Open Telegram and search for `@BotFather`
2. Start a chat with BotFather and send `/newbot`
3. Follow the instructions to create a new bot
4. Copy the API token provided by BotFather

### 3. Environment Setup

1. Clone this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Edit the `.env` file and add your API keys:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   OPENAI_API_KEY=your_openai_api_key
   PERPLEXITY_API_KEY=your_perplexity_api_key
   APIFY_API_TOKEN=your_apify_api_token
   DEEPL_API_KEY=your_deepl_api_key
   RIME_API_KEY=your_rime_api_key
   RIME_CALLER_ID=your_caller_id_number (optional)
   PORT=5000
   ```

### 4. Run the Bot

```
python app.py
```

The application will:
1. Start a Flask server
2. Create an ngrok tunnel to expose your local webhook
3. Register the webhook URL with Telegram
4. Start listening for incoming messages

## Usage

Once the bot is running, users can interact with it in their Telegram app:

1. Start a chat with your bot using the username you created
2. Send the `/start` command to get a welcome message
3. Ask questions about flights, destinations, or activities:
   - "Find flights from New York to London for next week"
   - "What are the best things to do in Tokyo?"
   - "Tell me about Berlin in May"
4. Make reservations by asking the bot to book for you:
   - "Book a table for dinner at Chez Marie in Paris for tomorrow at 7pm"
   - "Reserve a room at the Grand Hotel in Rome for May 15th for 3 nights"
   - "Get tickets to the Tokyo Sky Tree for next Tuesday"
5. Use the `/summary` command to get a compiled trip itinerary based on your conversation

## Making Reservations with Rime

The Voyagent bot can make actual phone calls to businesses using Rime's AI voice agents. When a user requests a reservation, the bot will:

1. Collect necessary details about the reservation
2. Initiate a phone call to the business
3. Have a natural conversation to make the booking
4. Return the confirmation details to the user

This feature works for:
- Restaurant reservations
- Hotel bookings
- Attraction ticket purchases
- Travel agency inquiries

To use this feature, you'll need to provide:
- The name of the business
- A valid phone number 
- Details like date, time, number of people, etc.

## Architecture

```
Telegram --> Flask /webhook --> LangChain Agent (MCP Runner) 
                           |--> Tool 1: Perplexity web search
                           |--> Tool 2: Apify flight / POI actors
                           |--> Tool 3: DeepL translation
                           |--> Tool 4: Rime reservation calls
                           '--> Local cache (JSON) + /summary formatter
```

## Demo Flow

For a quick 3-minute demo:
1. Ask about flights (e.g., "Find flights from Berlin to Rome")
2. Ask about activities (e.g., "What are popular attractions in Rome?")
3. Make a reservation (e.g., "Book a table at La Pergola in Rome for tomorrow at 8pm")
4. Type `/summary` to get your trip plan with confirmed reservations

## Extending the Bot

To add new tools or features:
1. Create a new tool implementation in the `Voyagent/tools/` directory
2. Register the tool in `agent_runner.py`
3. Update the system prompt to tell the agent when to use the new tool