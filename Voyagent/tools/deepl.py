import os
import json
import logging
import requests
from dotenv import load_dotenv
from langchain.tools import BaseTool

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class DeepLTranslateTool(BaseTool):
    name = "deepl_translate"
    description = """
    Translates text using the DeepL Translation API. Use this tool when the user asks for
    information in a language other than English or wants to translate text.
    
    Input should be in the format: "text: [text to translate], target_language: [language code]"
    
    Language codes: 
    BG - Bulgarian, CS - Czech, DA - Danish, DE - German, EL - Greek, EN - English,
    ES - Spanish, ET - Estonian, FI - Finnish, FR - French, HU - Hungarian,
    ID - Indonesian, IT - Italian, JA - Japanese, KO - Korean, LT - Lithuanian,
    LV - Latvian, NB - Norwegian, NL - Dutch, PL - Polish, PT - Portuguese,
    RO - Romanian, RU - Russian, SK - Slovak, SL - Slovenian, SV - Swedish,
    TR - Turkish, UK - Ukrainian, ZH - Chinese
    """
    
    def _run(self, query: str) -> str:
        """Translate text using DeepL API."""
        logger.info(f"TOOL: deepl_translate - Query: {query}")
        
        api_key = os.getenv("DEEPL_API_KEY")
        if not api_key:
            logger.error("DeepL API key not found")
            return "Error: DeepL API key not configured"
        
        # Parse query to extract text and target language
        params = self._parse_translate_query(query)
        
        if not params["text"]:
            return "Error: No text provided for translation"
        
        if not params["target_language"]:
            params["target_language"] = "EN"  # Default to English
        
        # In a real implementation, call the DeepL Translation API
        url = "https://api.deepl.com/v2/translate"
        
        headers = {
            "Authorization": f"DeepL-Auth-Key {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "text": [params["text"]],
            "target_lang": params["target_language"].upper()
        }
        
        try:
            # Uncomment for actual API call
            # response = requests.post(url, headers=headers, json=payload)
            # response.raise_for_status()
            # result = response.json()
            # translated_text = result["translations"][0]["text"]
            # return translated_text
            
            # For demo purposes, return mock translation
            mock_translation = self._get_mock_translation(params["text"], params["target_language"])
            return mock_translation
            
        except Exception as e:
            logger.error(f"Error calling DeepL API: {e}")
            return f"Error translating text: {str(e)}"
    
    def _parse_translate_query(self, query: str) -> dict:
        """Parse the translation query to extract text and target language."""
        params = {"text": "", "target_language": ""}
        
        for part in query.split(","):
            part = part.strip()
            
            if part.lower().startswith("text:"):
                params["text"] = part[5:].strip()
            elif part.lower().startswith("target_language:"):
                params["target_language"] = part[16:].strip()
        
        return params
    
    def _get_mock_translation(self, text: str, target_language: str) -> str:
        """Generate mock translation for demo purposes."""
        target_language = target_language.upper()
        
        # Very simple mock translations for demo
        translations = {
            "Hello! How can I help you plan your trip?": {
                "ES": "¡Hola! ¿Cómo puedo ayudarte a planificar tu viaje?",
                "FR": "Bonjour! Comment puis-je vous aider à planifier votre voyage?",
                "DE": "Hallo! Wie kann ich Ihnen bei der Planung Ihrer Reise helfen?",
                "IT": "Ciao! Come posso aiutarti a pianificare il tuo viaggio?",
                "JA": "こんにちは！あなたの旅行の計画をどのようにお手伝いできますか？",
                "ZH": "你好！我能怎样帮助你规划旅行？"
            },
            "The Eiffel Tower is a must-visit attraction in Paris.": {
                "ES": "La Torre Eiffel es una atracción que hay que visitar en París.",
                "FR": "La Tour Eiffel est une attraction incontournable à Paris.",
                "DE": "Der Eiffelturm ist eine Sehenswürdigkeit, die man in Paris unbedingt besuchen sollte.",
                "IT": "La Torre Eiffel è un'attrazione da non perdere a Parigi.",
                "JA": "エッフェル塔はパリで必見の観光スポットです。",
                "ZH": "埃菲尔铁塔是巴黎必游的景点。"
            }
        }
        
        # Check if we have a mock translation for this text
        if text in translations:
            if target_language in translations[text]:
                return translations[text][target_language]
        
        # If no mock translation available, indicate it's a mock
        return f"[Mock Translation to {target_language}] {text}"