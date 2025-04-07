# LangBot - Telegram Language Learning Bot

LangBot is a Telegram bot that helps users learn new languages by providing phonetic translations in group chats. Each user can set their own target language and choose whether to see translations.

## Features

- **Set Learning Language**: Choose the language you want to learn using `/setlanguage [language]`
- **Set Display Mode**: Control how translations are displayed with `/setmode [mode]`
  - `overlay`: Bot replies with messages showing translations
  - `off`: Disable translations (default)
- **Check Settings**: View your current settings with `/getsettings`
- **Automatic Translations**: The bot automatically translates messages in group chats and provides phonetic transliterations using English letters

## Setup Instructions

1. **Install Dependencies**
   ```
   pip install -r requirements.txt
   ```

2. **Get API Keys**
   - Create a Telegram bot using [BotFather](https://t.me/botfather) and get your bot token
   - Get a Google API key for Gemini from the [Google AI Studio](https://ai.google.dev/)

3. **Configure Environment Variables**
   - Create a `.env` file in the project root
   - Add your API keys:
     ```
     TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
     GOOGLE_API_KEY=your_google_api_key_here
     PORT=8080  # Required for Render deployment
     ```

4. **Run the Bot Locally**
   ```
   python langbot.py
   ```

5. **Add to Group Chat**
   - Add your bot to a group chat
   - Ensure the bot has permission to read messages and send replies

## Deployment on Render

1. **Create a Render account**
   - Sign up at [render.com](https://render.com)

2. **Connect your GitHub repository**
   - Push your code to GitHub
   - Connect your repository to Render

3. **Create a Web Service**
   - Choose the Web Service option
   - Select your repository
   - Configure the service:
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `python langbot.py`
     - **Environment Variables:** Add your `TELEGRAM_BOT_TOKEN` and `GOOGLE_API_KEY`
     - Render will automatically provide the `PORT` environment variable

4. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy your bot

5. **Verify Deployment**
   - The HTTP server built into the bot will respond on the assigned port
   - Your bot should now be operational on Telegram

## Usage

1. Start a private chat with the bot and use `/start` to get help
2. Set your target language with `/setlanguage [language]` (e.g., `/setlanguage Spanish`)
3. Choose your display mode with `/setmode [mode]` (e.g., `/setmode overlay`)
4. Check your current settings with `/getsettings`
5. The bot will automatically translate messages in the group chat according to your settings and display them with English phonetic transliterations

## Supported Languages

The bot supports all languages available through Google's Gemini API. You can specify any language name when setting your learning language.

## How It Works

LangBot uses Google's Gemini API to:
1. Translate messages from English to your target language
2. Create phonetic transliterations using English letters to help with pronunciation
3. Reply to original messages with these transliterations

## Data Storage

User settings are stored in a local JSON file (`user_settings.json`). Each user's settings include:
- Target language for learning
- Preferred display mode for translations (overlay or off)

### Note on Persistent Storage with Render
When deploying to Render, be aware that the filesystem is ephemeral. For persistent storage options:
1. Use Render's persistent disk feature
2. Consider migrating to a database solution

## Security Note

- API keys should be stored as environment variables, not in the code
- Never commit your `.env` file to version control (it's included in `.gitignore`)
- The bot only stores user IDs and preferences, not message content

## License

MIT 