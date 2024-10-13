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

# List of Telegram channel usernames
CHANNELS = [
    "From_hebron",  # Add more channels as needed
]

# Timezone for Israel Standard Time (IST)
ISRAEL_TZ = pytz.timezone('Asia/Jerusalem')

class TelegramService:
    def __init__(self):
        """
        Initializes the TelegramService with a persistent session file.
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

    async def read_messages_from_channel(self, channel_username: str, limit: int = 100, interval: int = 60) -> list[Message]:
        """
        Reads messages from a specified Telegram channel within the given time interval.
        :param channel_username: Username of the channel to read messages from.
        :param limit: Number of messages to fetch from the channel.
        :param interval: Time interval in minutes to filter messages.
        :return: List of filtered message objects.
        """
        try:
            channel = await self._client.get_entity(channel_username)
            messages = await self._client.get_messages(channel, limit=limit)

            # Current UTC time
            current_time = datetime.utcnow().replace(tzinfo=pytz.UTC)
            # Threshold time: messages from the last 'interval' minutes (in this case, 60 minutes)
            threshold_time = current_time - timedelta(minutes=interval)

            # Filter messages within the last 'interval' minutes
            last_interval_messages = [
                m for m in messages if m.date and m.date >= threshold_time
            ]

            return last_interval_messages
        except Exception as e:
            print(f"Error reading messages from channel {channel_username}: {e}")
            return []

    async def fetch_messages_from_channels(self):
        """
        Fetches messages from multiple Telegram channels and prints them in Israel Standard Time (IST).
        """
        messages: list[Message] = []
        # Start client and fetch messages
        async with self._client:
            for channel in CHANNELS:
                # Fetch messages from each channel for the last 60 minutes
                channel_messages = await self.read_messages_from_channel(
                    channel_username=channel,
                    limit=100,
                    interval=60,  # Last 60 minutes
                )
                messages.extend(channel_messages)

        # Print the filtered messages with timestamps converted to Israel Standard Time (IST)
        for m in messages:
            # Convert the UTC timestamp to Israel Standard Time
            ist_time = m.date.astimezone(ISRAEL_TZ)
            print(f"[{ist_time.strftime('%Y-%m-%d %H:%M:%S')}] {m.message}")  # Printing date and message content

        return messages

# Run the client
async def main():
    telegram_service = TelegramService()
    await telegram_service.start()  # Start and authenticate
    await telegram_service.fetch_messages_from_channels()  # Fetch and print messages
    await telegram_service.disconnect()  # Disconnect the client

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error running the main event loop: {e}")
