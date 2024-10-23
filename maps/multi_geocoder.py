import os
from dotenv import load_dotenv
import requests
import json
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

    def get_opencage_coordinates(self, place):
        url = f'https://api.opencagedata.com/geocode/v1/json?q={place}&key={self.opencage_api_key}'
        print(f"Fetching OpenCage coordinates for: {place}")
        response = requests.get(url)
        try:
            data = response.json()
            return data
        except json.JSONDecodeError as e:
            print(f"OpenCage response error: {response.text}")
            return {'error': 'Failed to parse OpenCage response'}

    def get_nominatim_coordinates(self, place):
        params = {'q': place, 'format': 'json'}
        headers = {'User-Agent': 'YourAppName/1.0 (your.email@example.com)'}  # Add custom User-Agent
        print(f"Fetching Nominatim coordinates for: {place}")
        response = requests.get(self.nominatim_url, params=params, headers=headers)
        try:
            data = response.json()
            return data
        except json.JSONDecodeError as e:
            print(f"Nominatim response error: {response.text}")
            return {'error': 'Failed to parse Nominatim response'}

    def get_locationiq_coordinates(self, place):
        url = f'https://us1.locationiq.com/v1/search.php?key={self.locationiq_api_key}&q={place}&format=json'
        print(f"Fetching LocationIQ coordinates for: {place}")
        response = requests.get(url)
        try:
            data = response.json()
            return data
        except json.JSONDecodeError as e:
            print(f"LocationIQ response error: {response.text}")
            return {'error': 'Failed to parse LocationIQ response'}

    def get_all_coordinates(self, place):
        result = {}
        result['OpenCage'] = self.get_opencage_coordinates(place)
        result['Nominatim'] = self.get_nominatim_coordinates(place)
        result['LocationIQ'] = self.get_locationiq_coordinates(place)
        
        return json.dumps(result, indent=4)