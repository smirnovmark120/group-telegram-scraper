import os
import asyncio
from datetime import datetime, timedelta
import pytz
from telethon import TelegramClient
from dotenv import load_dotenv
from telethon.tl.patched import Message
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from the .env file
load_dotenv()

# Read values from .env
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')

# Define a directory for the session file
session_dir = os.path.join(os.getcwd(), 'telegram_sessions')
os.makedirs(session_dir, exist_ok=True)

# Set the session file path
SESSION_NAME = os.path.join(session_dir, 'my_session.session')

# Timezone for Israel Standard Time (IST)
ISRAEL_TZ = pytz.timezone('Asia/Jerusalem')

class TelegramScraper:
    def __init__(self):
        try:
            self._client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        except Exception as e:
            logging.error(f"Error initializing Telegram client: {e}")
            raise

    async def start(self):
        try:
            await self._client.connect()
            if not await self._client.is_user_authorized():
                if PHONE_NUMBER.startswith('123456:'):
                    await self._client.start(bot_token=PHONE_NUMBER)
                else:
                    await self._client.send_code_request(PHONE_NUMBER)
                    code = input('Enter the code you received: ')
                    await self._client.sign_in(PHONE_NUMBER, code)
        except Exception as e:
            logging.error(f"Error starting Telegram client: {e}")
            raise

    async def disconnect(self):
        await self._client.disconnect()

    async def read_messages_from_channel(self, channel_username: str, threshold_time: datetime) -> list[dict]:
        try:
            channel = await self._client.get_entity(channel_username)
            result = []
            total_messages = 0
            
            offset_id = 0
            oldest_message_date = None
            newest_message_date = None

            while True:
                logging.info(f"Fetching batch of messages from {channel_username} (offset_id: {offset_id})")
                messages = await self._client.get_messages(channel, limit=100, offset_id=offset_id)
                
                if not messages:
                    logging.info(f"No more messages to fetch from {channel_username}")
                    break

                batch_oldest = messages[-1].date
                batch_newest = messages[0].date
                
                logging.info(f"Batch time range: {batch_oldest} to {batch_newest}")

                if oldest_message_date is None or batch_oldest < oldest_message_date:
                    oldest_message_date = batch_oldest
                if newest_message_date is None or batch_newest > newest_message_date:
                    newest_message_date = batch_newest

                for message in messages:
                    if message.date and message.date >= threshold_time:
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

                        if message.media:
                            media_type = type(message.media).__name__
                            message_json['media'].append({
                                'media_type': media_type,
                                'media_id': message.id
                            })

                        result.append(message_json)
                        total_messages += 1
                    elif message.date < threshold_time:
                        logging.info(f"Reached messages older than threshold. Stopping.")
                        break

                if messages[-1].date < threshold_time:
                    break

                offset_id = messages[-1].id

            logging.info(f"Total messages fetched from {channel_username}: {total_messages}")
            logging.info(f"Time range of fetched messages: {oldest_message_date} to {newest_message_date}")

            return result, oldest_message_date

        except Exception as e:
            logging.error(f"Error reading messages from channel {channel_username}: {e}")
            return [], None

    async def fetch_messages(self, channels: list, time_window_minutes: int) -> list:
        messages = []
        current_time = datetime.utcnow().replace(tzinfo=pytz.UTC)
        threshold_time = current_time - timedelta(minutes=time_window_minutes)

        async with self._client:
            for channel in channels:
                channel_messages, oldest_message_date = await self.read_messages_from_channel(channel, threshold_time)
                messages.extend(channel_messages)

                if oldest_message_date and oldest_message_date > threshold_time:
                    logging.warning("The oldest message is newer than the threshold time. Checking for missing messages...")
                    # Check if there are any messages in the missing time range
                    missing_messages = await self._client.get_messages(channel, offset_date=threshold_time, limit=1)
                    if not missing_messages:
                        logging.info("No messages found in the missing time range. The channel might not have had any messages during that period.")
                    else:
                        logging.warning(f"Found a message in the missing time range. Oldest message: {missing_messages[0].date}")

        # Final check
        if messages:
            oldest_message = min(messages, key=lambda x: datetime.strptime(x['timestamp'], '%Y-%m-%d %H:%M:%S'))
            newest_message = max(messages, key=lambda x: datetime.strptime(x['timestamp'], '%Y-%m-%d %H:%M:%S'))
            
            logging.info(f"Overall time range of fetched messages:")
            logging.info(f"Oldest: {oldest_message['timestamp']}")
            logging.info(f"Newest: {newest_message['timestamp']}")
            logging.info(f"Expected range: {threshold_time} to {current_time}")

        return messages

async def scrape_telegram_messages(channels: list, time_window_minutes: int):
    scraper = TelegramScraper()
    await scraper.start()
    result = await scraper.fetch_messages(channels, time_window_minutes)
    await scraper.disconnect()
    return result

if __name__ == '__main__':
    channels = ["From_hebron"]  # Add more channels as needed
    time_window_minutes = 5000  # Fetch messages from the last 60 minutes

    try:
        result = asyncio.run(scrape_telegram_messages(channels, time_window_minutes))

        # Print the number of messages loaded
        print(f"Number of messages loaded: {len(result)}")
    except Exception as e:
        logging.error(f"Error running the main event loop: {e}")
    
    output_file = "telegram_messages.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    logging.info(f"Messages saved to {output_file}")
