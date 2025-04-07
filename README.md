# LangBot - Telegram Language Learning Bot

LangBot is a Telegram bot that helps users learn new languages by providing phonetic translations in group chats. Each user can set their own target language and choose whether to see translations.

![a_colorful_speech_image](https://github.com/user-attachments/assets/c6f71349-0469-4ad7-a189-9440e2035436)


## Try the Bot Now!

A live version of this bot is already hosted and ready to use! Just add [@msg_langbot](https://t.me/msg_langbot) to your group chat or send a direct message to get started.

The hosted bot offers all features described in this README and is maintained for reliable, 24/7 operation. No setup required - just add it to your group!

### Quick Start Guide

1. Add [@msg_langbot](https://t.me/msg_langbot) to your group chat
2. Make the bot an admin in your group
3. Message the bot directly with `/start` to see available commands
4. Set your learning language: `/setlanguage Spanish` (or any language)
5. Turn on translations: `/setmode overlay`
6. Check your settings: `/getsettings`
7. Return to your group and watch as messages get translated with phonetic guides!

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
     REDIS_URL=your_redis_url_here  # For persistent storage
     ```

4. **Run the Bot Locally**
   ```
   python langbot.py
   ```

5. **Add to Group Chat**
   - Add your bot to a group chat
   - **Important**: Make the bot an admin in the group
   - Ensure the bot has permission to read messages and send replies

6. **Configure Bot Privacy Settings**
   - Send `/mybots` to BotFather
   - Select your bot
   - Go to "Bot Settings" > "Group Privacy"
   - Set it to DISABLED (this allows the bot to see all messages in groups)

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
     - Render will automatically provide the `PORT` and `RENDER_EXTERNAL_URL` environment variables

4. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy your bot

5. **Webhook Configuration**
   - The bot will automatically set up a webhook using the Render external URL
   - No additional configuration is needed as the bot detects if it's running on Render

## Important Note on Multiple Instances

Only one instance of your bot can poll for updates from the Telegram API at a time. If you deploy multiple instances, or run both locally and on Render, you'll get the "terminated by other getUpdates request" error. To solve this:

1. Stop any locally running instances when deploying to Render
2. If you need multiple instances, use webhook mode (the default on Render)
3. If you have multiple Render instances, pause or delete all but one

## Usage

1. Start a private chat with the bot and use `/start` to get help
2. Set your target language with `/setlanguage [language]` (e.g., `/setlanguage Spanish`)
3. Choose your display mode with `/setmode [mode]` (e.g., `/setmode overlay`)
4. Check your current settings with `/getsettings`
5. The bot will automatically translate messages in the group chat according to your settings and display them with English phonetic transliterations

## Troubleshooting

If translations aren't working in your group:

1. **Verify Bot Admin Status**: The bot must be an admin in your group to see all messages
2. **Check Privacy Mode**: Make sure you've disabled privacy mode with BotFather
3. **User Settings**: Ensure at least one user (not the message sender) has:
   - Set a language using `/setlanguage`
   - Set mode to `overlay` using `/setmode overlay`
4. **Send Test Messages**: Have someone else (not you) send messages while you have translation mode on

## Supported Languages

The bot supports all languages available through Google's Gemini API. You can specify any language name when setting your learning language.

## How It Works

LangBot uses Google's Gemini API to:
1. Translate messages from English to your target language
2. Create phonetic transliterations using English letters to help with pronunciation
3. Reply to original messages with these transliterations

## Data Storage

User settings are stored in Redis, a fast, in-memory data store that provides persistent storage across application restarts. Each user's settings include:
- Target language for learning
- Preferred display mode for translations (overlay or off)

The bot uses the Redis key format `user:{user_id}` to store JSON-serialized user settings.

### Redis Configuration

The bot requires a Redis server for persistent storage. You can use:
1. **Upstash** (recommended for Render deployment): A serverless Redis service with a free tier
2. **Redis Cloud**: Another managed Redis service
3. **Self-hosted Redis**: For local development or your own server

To configure Redis:
1. Create a Redis instance (e.g., on Upstash.com)
2. Add your Redis URL to the `.env` file:
   ```
   REDIS_URL=redis://default:password@hostname:port
   ```
3. For TLS connections (like Upstash), the bot automatically enables SSL

### Storage Considerations
Redis provides several advantages over the previous file-based storage:
1. **True Persistence**: User settings persist across application restarts
2. **Atomic Operations**: Reduces the risk of data corruption
3. **Performance**: In-memory storage is significantly faster than file operations
4. **Scalability**: Works well for large numbers of users

## Security Note

- API keys should be stored as environment variables, not in the code
- Never commit your `.env` file to version control (it's included in `.gitignore`)
- The bot only stores user IDs and preferences, not message content

## License

MIT 
