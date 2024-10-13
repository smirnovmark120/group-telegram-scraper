import os
import asyncio
from datetime import datetime, timedelta
import pytz
from telethon import TelegramClient
from dotenv import load_dotenv
from telethon.tl.patched import Message

# Load environment variables from the .env file
load_dotenv()

# Read values from .env
API_ID = os.getenv('API_ID')  # Your API_ID from .env
API_HASH = os.getenv('API_HASH')  # Your API_HASH from .env
PHONE_NUMBER = os.getenv('PHONE_NUMBER')  # Your phone number or bot token from .env

# Define a directory for the session file
session_dir = os.path.join(os.getcwd(), 'telegram_sessions')
os.makedirs(session_dir, exist_ok=True)  # Create the directory if it doesn't exist

# Set the session file path
SESSION_NAME = os.path.join(session_dir, 'my_session.session')

# Timezone for Israel Standard Time (IST)
ISRAEL_TZ = pytz.timezone('Asia/Jerusalem')


class TelegramScraper:
    def __init__(self):
        """
        Initializes the TelegramScraper with a persistent session file.
        """
        try:
            self._client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        except Exception as e:
            print(f"Error initializing Telegram client: {e}")
            raise

    async def start(self):
        """
        Starts and connects the Telegram client.
        """
        try:
            await self._client.connect()

            # If the client is not yet authorized, authorize it
            if not await self._client.is_user_authorized():
                # If using a bot token, log in with the bot token
                if PHONE_NUMBER.startswith('123456:'):  # Example of a bot token format
                    await self._client.start(bot_token=PHONE_NUMBER)
                else:
                    # Otherwise, request code for phone number login
                    await self._client.send_code_request(PHONE_NUMBER)
                    code = input('Enter the code you received: ')
                    await self._client.sign_in(PHONE_NUMBER, code)
        except Exception as e:
            print(f"Error starting Telegram client: {e}")
            raise

    async def disconnect(self):
        """
        Disconnects the Telegram client.
        """
        await self._client.disconnect()

    async def read_messages_from_channel(self, channel_username: str, threshold_time: datetime) -> list[dict]:
        """
        Reads messages from a specified Telegram channel within the given time interval.
        :param channel_username: Username of the channel to read messages from.
        :param threshold_time: The threshold time to filter messages after.
        :return: List of message objects in JSON format.
        """
        try:
            channel = await self._client.get_entity(channel_username)
            messages = await self._client.get_messages(channel, limit=100)

            # Filter messages after the threshold time
            filtered_messages = [
                m for m in messages if m.date and m.date >= threshold_time
            ]

            # Create a structured JSON result for each message
            result = []
            for message in filtered_messages:
                ist_time = message.date.astimezone(ISRAEL_TZ)
                message_json = {
                    'channel': channel_username,
                    'message_id': message.id,
                    'timestamp': ist_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'message': message.message or '',
                    'metadata': {
                        'sender_id': message.sender_id,
                        'message_type': type(message).__name__
                    },
                    'media': []
                }

                # Check if the message contains media
                if message.media:
                    media_type = type(message.media).__name__
                    message_json['media'].append({
                        'media_type': media_type,
                        'media_id': message.id
                    })

                result.append(message_json)

            return result

        except Exception as e:
            print(f"Error reading messages from channel {channel_username}: {e}")
            return []

    async def fetch_messages(self, channels: list, time_window_minutes: int) -> list:
        """
        Fetches messages from multiple Telegram channels and returns a JSON-formatted result.
        :param channels: List of Telegram channel usernames.
        :param time_window_minutes: Time interval in minutes to filter messages.
        :return: JSON list of messages, metadata, and media references.
        """
        messages = []
        # Calculate the threshold time
        current_time = datetime.utcnow().replace(tzinfo=pytz.UTC)
        threshold_time = current_time - timedelta(minutes=time_window_minutes)

        # Start client and fetch messages from channels
        async with self._client:
            for channel in channels:
                channel_messages = await self.read_messages_from_channel(channel, threshold_time)
                messages.extend(channel_messages)

        return messages


# Function to be called to scrape messages
async def scrape_telegram_messages(channels: list, time_window_minutes: int):
    scraper = TelegramScraper()
    await scraper.start()  # Start and authenticate
    result = await scraper.fetch_messages(channels, time_window_minutes)
    await scraper.disconnect()  # Disconnect the client
    return result

# Example usage
if __name__ == '__main__':
    channels = ["From_hebron"]  # Add more channels as needed
    time_window_minutes = 60  # Fetch messages from the last 60 minutes

    try:
        result = asyncio.run(scrape_telegram_messages(channels, time_window_minutes))
        # Print the result as JSON
        import json
        print(json.dumps(result, indent=4))
    except Exception as e:
        print(f"Error running the main event loop: {e}")
        
    # Specify the output JSON file path
    output_file = "telegram_messages.json"

    # Save the result as a local JSON file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    print(f"Messages saved to {output_file}")
