import os
from dotenv import load_dotenv
import json
import aiohttp
import asyncio
from timer_meta import TimerMeta

class MultiGeocoder(metaclass=TimerMeta):
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()

        # Fetch API credentials from environment variables
        self.opencage_api_key = os.getenv('OPENCAGE_API_KEY')
        self.locationiq_api_key = os.getenv('LOCATIONIQ_API_KEY')
        
        # No keys needed for Nominatim
        self.nominatim_url = 'https://nominatim.openstreetmap.org/search'

    async def get_opencage_coordinates(self, session, place):
        url = f'https://api.opencagedata.com/geocode/v1/json?q={place}&key={self.opencage_api_key}'
        print(f"Fetching OpenCage coordinates for: {place}")
        try:
            async with session.get(url) as response:
                data = await response.json()
                return data
        except aiohttp.ClientError as e:
            print(f"OpenCage response error: {e}")
            return {'error': 'Failed to fetch OpenCage data'}
        except json.JSONDecodeError as e:
            print(f"OpenCage response parsing error: {e}")
            return {'error': 'Failed to parse OpenCage response'}

    async def get_nominatim_coordinates(self, session, place):
        params = {'q': place, 'format': 'json'}
        headers = {'User-Agent': 'YourAppName/1.0 (your.email@example.com)'}  # Add custom User-Agent
        print(f"Fetching Nominatim coordinates for: {place}")
        try:
            async with session.get(self.nominatim_url, params=params, headers=headers) as response:
                data = await response.json()
                return data
        except aiohttp.ClientError as e:
            print(f"Nominatim response error: {e}")
            return {'error': 'Failed to fetch Nominatim data'}
        except json.JSONDecodeError as e:
            print(f"Nominatim response parsing error: {e}")
            return {'error': 'Failed to parse Nominatim response'}

    async def get_locationiq_coordinates(self, session, place):
        url = f'https://us1.locationiq.com/v1/search.php?key={self.locationiq_api_key}&q={place}&format=json'
        print(f"Fetching LocationIQ coordinates for: {place}")
        try:
            async with session.get(url) as response:
                data = await response.json()
                return data
        except aiohttp.ClientError as e:
            print(f"LocationIQ response error: {e}")
            return {'error': 'Failed to fetch LocationIQ data'}
        except json.JSONDecodeError as e:
            print(f"LocationIQ response parsing error: {e}")
            return {'error': 'Failed to parse LocationIQ response'}

    async def get_all_coordinates(self, place):
        async with aiohttp.ClientSession() as session:
            # Create tasks for fetching coordinates concurrently
            tasks = [
                self.get_opencage_coordinates(session, place),
                self.get_nominatim_coordinates(session, place),
                self.get_locationiq_coordinates(session, place)
            ]
            
            # Run the tasks concurrently and gather results
            opencage_result, nominatim_result, locationiq_result = await asyncio.gather(*tasks)
            
            # Combine the results into a single dictionary
            result = {
                'OpenCage': opencage_result,
                'Nominatim': nominatim_result,
                'LocationIQ': locationiq_result
            }
            
            return json.dumps(result, indent=4)
        
# # Example usage: Wrapping the async function to be run synchronously
# def run_geocoder(place):
#     geocoder = MultiGeocoder()
#     return asyncio.run(geocoder.get_all_coordinates(place))