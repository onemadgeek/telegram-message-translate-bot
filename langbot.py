import os
import json
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
from openai import OpenAI
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from flask import Flask, request

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get API keys from environment
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Initialize Google client (using OpenAI client)
client = OpenAI(
    api_key=GOOGLE_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# Test Google API connectivity
def test_google_api():
    try:
        logger.info("Testing Google Gemini API connectivity...")
        response = client.chat.completions.create(
            model="gemini-2.0-flash",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'API connection successful' in one short sentence."}
            ],
            max_tokens=20
        )
        result = response.choices[0].message.content.strip()
        logger.info(f"Google API test result: {result}")
        return True
    except Exception as e:
        logger.error(f"Google API test failed: {e}")
        return False

# User settings storage
USER_SETTINGS_FILE = 'user_settings.json'

# Valid modes
VALID_MODES = ['overlay', 'off']

# Initialize Flask app for health checks
app = Flask(__name__)

@app.route('/')
def health():
    return 'Bot is running'

# Helper function to load user settings
def load_user_settings():
    try:
        if os.path.exists(USER_SETTINGS_FILE):
            with open(USER_SETTINGS_FILE, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Error loading user settings: {e}")
        return {}

# Helper function to save user settings
def save_user_settings(settings):
    try:
        with open(USER_SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving user settings: {e}")

# Initialize user settings
user_settings = load_user_settings()

# Helper function to get user settings
def get_user_settings(user_id):
    user_id_str = str(user_id)
    if user_id_str not in user_settings:
        user_settings[user_id_str] = {
            "language": None,
            "mode": "off"  # Default to off mode
        }
        save_user_settings(user_settings)
    return user_settings[user_id_str]

# Helper function to update user settings
def update_user_settings(user_id, key, value):
    user_id_str = str(user_id)
    if user_id_str not in user_settings:
        user_settings[user_id_str] = {
            "language": None,
            "mode": "off"
        }
    user_settings[user_id_str][key] = value
    save_user_settings(user_settings)

# Function to extract key phrases from a message
def extract_key_phrases(text, max_phrases=5):
    # For short messages, just return the whole text
    if len(text.split()) <= max_phrases:
        return [{'original': text, 'start_pos': 0, 'length': len(text)}]
    
    # Split text into words
    words = text.split()
    
    # Create a list of candidate words
    candidates = []
    
    # Process individual words
    for word in words:
        clean_word = word.strip('.,!?;:()"\'')
        if len(clean_word) > 1:  # Include most words, even common ones
            candidates.append({
                'original': word,
                'start_pos': text.find(word),
                'length': len(word)
            })
    
    # Return a random sample of words to make translations varied
    import random
    if len(candidates) > max_phrases:
        return random.sample(candidates, max_phrases)
    return candidates

# Function to translate text using Google Gemini API
def translate_text(text, target_language):
    try:
        # Import re at the beginning of the function
        import re
        import traceback
        
        logger.info(f"Translating sentence to {target_language} with English pronunciation: '{text}'")
        
        # Create the prompt
        system_prompt = (
            "You are an expert linguistic assistant specializing in **phonetic transliteration** of translations.\n"
            "Your task is to FIRST translate the given English text into the specified target language, "
            "and THEN output ONLY the Romanized (English letter) phonetic transliteration of THAT TRANSLATION, "
            "optimized for pronunciation by a native English speaker.\n\n"
            "Follow these examples STRICTLY:\n"

            # --- Tamil Examples ---
            "Example 1 (Tamil):\n"
            "User asks for: 'Hello' in Tamil\n"
            "Your thought process: 'Hello' in Tamil is 'Vanakkam' (வணக்கம்). Phonetic transliteration is 'Vanakkam'.\n"
            "Your response: Vanakkam\n\n"

            "Example 2 (Tamil):\n"
            "User asks for: 'Thank you' in Tamil\n"
            "Your thought process: 'Thank you' in Tamil is 'Nandri' (நன்றி). Phonetic transliteration is 'Nandri'.\n"
            "Your response: Nandri\n\n"

            "Example 3 (Tamil):\n"
            "User asks for: 'Okay' in Tamil\n"
            "Your thought process: 'Okay' in Tamil is 'Sari' (சரி). Phonetic transliteration is 'Sari'.\n"
            "Your response: Sari\n\n"

            # --- Telugu Examples ---
            "Example 4 (Telugu):\n"
            "User asks for: 'Hello' in Telugu\n"
            "Your thought process: 'Hello' in Telugu is 'Namaskaram' (నమస్కారం). Phonetic transliteration is 'Namaskaram'.\n"
            "Your response: Namaskaram\n\n"

            "Example 5 (Telugu):\n"
            "User asks for: 'Water' in Telugu\n"
            "Your thought process: 'Water' in Telugu is 'Neellu' (నీళ్ళు). Phonetic transliteration is 'Neellu'.\n"
            "Your response: Neellu\n\n"

            # --- Spanish Examples ---
            "Example 6 (Spanish):\n"
            "User asks for: 'Good morning' in Spanish\n"
            "Your thought process: 'Good morning' in Spanish is 'Buenos días'. Phonetic transliteration is 'Bway-nos dee-ahs'.\n"
            "Your response: Bway-nos dee-ahs\n\n"

            "Example 7 (Spanish):\n"
            "User asks for: 'Thank you' in Spanish\n"
            "Your thought process: 'Thank you' in Spanish is 'Gracias'. Phonetic transliteration is 'Grah-see-us'.\n"
            "Your response: Grah-see-us\n\n"

            # --- French Examples ---
            "Example 8 (French):\n"
            "User asks for: 'Hello' in French\n"
            "Your thought process: 'Hello' in French is 'Bonjour'. Phonetic transliteration is 'Bon-zhoor'.\n"
            "Your response: Bon-zhoor\n\n"

            "Example 9 (French):\n"
            "User asks for: 'Goodbye' in French\n"
            "Your thought process: 'Goodbye' in French is 'Au revoir'. Phonetic transliteration is 'Oh ruh-vwahr'.\n"
            "Your response: Oh ruh-vwahr\n\n"

            # --- Japanese Example ---
            "Example 10 (Japanese):\n"
            "User asks for: 'Thank you' in Japanese\n"
            "Your thought process: 'Thank you' in Japanese is 'Arigatou' (ありがとう). Phonetic transliteration is 'Ah-ree-gah-toh'.\n"
            "Your response: Ah-ree-gah-toh\n\n"

            # --- End Examples ---
            "IMPORTANT: Always follow the two steps: 1. Translate to the target language. 2. Provide ONLY the English letter phonetic transliteration of that translation.\n"
            "Strictly adhere to the output format constraints: only the English letter transliteration of the translation, no native script, no explanations, no quotes."
        )
        user_prompt = (
            f"Translate the following English text into {target_language} and provide ONLY the phonetic transliteration as shown in the examples:\n"
            f"\"{text}\""
        )
        
        # Log the complete prompt
        logger.info(f"PROMPT - System: {system_prompt}")
        logger.info(f"PROMPT - User: {user_prompt}")
        
        # Log completion parameters
        completion_params = {
            "model": "gemini-2.0-flash",
            "n": 1,
            "temperature": 0.1,
            "max_tokens": 150
        }
        logger.info(f"COMPLETION PARAMS: {completion_params}")
        
        response = client.chat.completions.create(
            model=completion_params["model"],
            n=completion_params["n"],
            messages=[
                {
                    "role": "system", 
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": user_prompt
                }
            ],
            temperature=completion_params["temperature"],
            max_tokens=completion_params["max_tokens"]
        )
        
        result = response.choices[0].message.content.strip()
        
        # Log the raw response
        logger.info(f"RAW RESPONSE: {result}")
        
        # Log information about the response
        logger.info(f"RESPONSE INFO - Model: {getattr(response, 'model', 'unknown')}, Finish Reason: {getattr(response.choices[0], 'finish_reason', 'unknown')}")
        
        logger.info(f"Translation result: '{text}' → '{result}'")
        
        # Clean up the result if needed
        # Remove any quotes, headings, etc.
        result = re.sub(r'^["\']*|["\']*$', '', result)  # Remove quotes at beginning/end
        result = re.sub(r'^Translation:|^Pronunciation:|^Transliteration:|^In English:', '', result, flags=re.IGNORECASE).strip()  # Remove common prefixes
        result = re.sub(r'[\u0900-\u097F\u0980-\u09FF\u0A00-\u0A7F\u0A80-\u0AFF\u0B00-\u0B7F\u0B80-\u0BFF\u0C00-\u0C7F\u0C80-\u0CFF\u0D00-\u0D7F]', '', result)  # Remove any native script characters
        
        # Log the cleaned result
        if result != response.choices[0].message.content.strip():
            logger.info(f"CLEANED RESULT: {result}")
        
        return result
                
    except Exception as e:
        logger.error(f"Translation error: {e}")
        logger.error(traceback.format_exc())
        return text  # Return original text if translation fails

# Command handler for /start
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        'Hello! I am Message Translate, your language learning assistant.\n\n'
        'Use /setlanguage [language] to set your learning language.\n'
        'Use /setmode [overlay|off] to set how you want to see translations.\n'
        '  - overlay: see translations in the chat\n'
        '  - off: disable translations (default)\n\n'
        'Use /getsettings to view your current settings.'
    )

# Command handler for /setlanguage
def set_language(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    
    if not context.args:
        update.message.reply_text('Please specify a language, e.g., /setlanguage Spanish')
        return
        
    language = ' '.join(context.args)
    
    # Accept any language without validation
    update_user_settings(user_id, 'language', language)
    update.message.reply_text(f'Your learning language has been set to {language}.')

# Command handler for /setmode
def set_mode(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    
    if not context.args:
        update.message.reply_text(f'Please specify a mode: /setmode [overlay|off]')
        return
    
    mode = context.args[0].lower()
    
    if mode not in VALID_MODES:
        update.message.reply_text(f'Invalid mode. Please choose from: overlay, off')
        return
    
    update_user_settings(user_id, 'mode', mode)
    
    if mode == 'overlay':
        update.message.reply_text(f'Your translation mode has been set to overlay. You will see translations in chat.')
    else:
        update.message.reply_text(f'Your translation mode has been set to off. You will not see any translations.')

# Command handler for /getsettings
def get_settings(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    settings = get_user_settings(user_id)
    
    language = settings['language'] or 'Not set'
    mode = settings['mode']
    
    mode_description = "Active (overlay)" if mode == "overlay" else "Inactive (off)"
    
    update.message.reply_text(
        f'Your current settings:\n'
        f'Learning language: {language}\n'
        f'Translation mode: {mode_description}'
    )

# Message handler for processing group messages
def process_message(update: Update, context: CallbackContext) -> None:
    # Skip processing if not in a group
    if update.effective_chat.type not in ['group', 'supergroup']:
        logger.info(f"Skipping message - not in a group chat")
        return
        
    # Get message info
    message = update.message
    sender_id = update.effective_user.id
    chat_id = update.effective_chat.id
    message_id = message.message_id
    message_text = message.text or ''
    
    # Log incoming message
    sender_username = update.effective_user.username or f"User{sender_id}"
    chat_title = update.effective_chat.title or f"Chat{chat_id}"
    logger.info(f"Message received in '{chat_title}' from @{sender_username}: '{message_text[:50]}{'...' if len(message_text) > 50 else ''}'")
    
    if not message_text:
        logger.info("Skipping empty message")
        return
    
    # Debug: Log all current user settings
    logger.info(f"Current user settings: {user_settings}")
    
    # Process message for each user in the group
    users_count = 0
    translation_count = 0
    
    for user_id_str, settings in user_settings.items():
        user_id = int(user_id_str)
        users_count += 1
        
        # Skip if this is the sender or if language is not set or mode is off
        if user_id == sender_id:
            logger.info(f"Skipping User{user_id} - message sender")
            continue
            
        if not settings['language']:
            logger.info(f"Skipping User{user_id} - no language set")
            continue
            
        if settings['mode'] == 'off':
            logger.info(f"Skipping User{user_id} - mode is off")
            continue
        
        logger.info(f"Processing for User{user_id} learning {settings['language']}")
        
        # Translate the entire message
        try:
            translated = translate_text(message_text, settings['language'])
            
            if translated != message_text and translated.strip() != '':
                logger.info(f"Translation successful: '{message_text}' → '{translated}'")
                
                formatted_message = f"{translated}"
                
                logger.info(f"Sending overlay translation to chat")
                context.bot.send_message(
                    chat_id=chat_id,
                    text=formatted_message,
                    parse_mode=ParseMode.HTML,
                    reply_to_message_id=message_id
                )
                translation_count += 1
            else:
                logger.info(f"No useful translation generated or translation matches original")
        except Exception as e:
            logger.error(f"Error during translation or sending: {e}")
    
    logger.info(f"Finished processing message {message_id} - Processed {users_count} users, sent {translation_count} translations")

def error_handler(update: Update, context: CallbackContext) -> None:
    logger.error(f"Update {update} caused error {context.error}")

def main() -> None:
    # Create the Updater
    # Test Google API connectivity at startup
    api_working = test_google_api()
    if not api_working:
        logger.error("!!! WARNING: Google API connection failed. Translations will not work !!!")
    else:
        logger.info("Google API connection successful. Translations should work correctly.")
    updater = Updater(TELEGRAM_TOKEN)
    
    # Get the dispatcher
    dispatcher = updater.dispatcher
    
    # Add command handlers with allowance for username suffix
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("setlanguage", set_language))
    dispatcher.add_handler(CommandHandler("setmode", set_mode))
    dispatcher.add_handler(CommandHandler("getsettings", get_settings))
    
    # Add message handler
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, process_message))
    
    # Add error handler
    dispatcher.add_error_handler(error_handler)
    
    # Determine if running on Render
    is_render = os.getenv('RENDER') == 'true'
    
    # Use PORT environment variable for both Flask and webhook
    port = int(os.getenv('PORT', 8080))
    
    # Start Flask server in a separate thread for health checks
    def run_flask():
        app.run(host='0.0.0.0', port=port)
    
    if is_render:
        # Use webhook mode for Render deployment
        render_external_url = os.getenv('RENDER_EXTERNAL_URL')
        if render_external_url:
            # Set webhook using Render's external URL
            updater.start_webhook(
                listen="0.0.0.0",
                port=port,
                url_path=TELEGRAM_TOKEN,
                webhook_url=f"{render_external_url}/{TELEGRAM_TOKEN}"
            )
            logger.info(f"Bot started in webhook mode with URL: {render_external_url}/{TELEGRAM_TOKEN}")
            
            # Only start Flask after webhook is set up
            flask_thread = threading.Thread(target=run_flask, daemon=True)
            flask_thread.start()
            logger.info(f"Health check server started on port {port}")
        else:
            # Fallback to polling mode if no external URL
            updater.start_polling()
            logger.info(f"Bot started in polling mode (fallback)")
            
            # Start Flask for health checks
            flask_thread = threading.Thread(target=run_flask, daemon=True)
            flask_thread.start()
            logger.info(f"Health check server started on port {port}")
    else:
        # Local development - use polling
        updater.start_polling()
        logger.info('Bot started in polling mode (local development)')
        
        # Start Flask on a different port for local development
        dev_port = 5000
        def run_flask_dev():
            app.run(host='0.0.0.0', port=dev_port)
        
        flask_thread = threading.Thread(target=run_flask_dev, daemon=True)
        flask_thread.start()
        logger.info(f"Health check server started on port {dev_port} (local development)")
    
    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main() 