import requests
import json
import logging
import aiohttp
import asyncio
from timer_meta import TimerMeta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeocodeDataExtractor(metaclass=TimerMeta):
    def __init__(self, data):
        self.data = data

    async def fetch_wikidata_aliases(self, wikidata_id):
        """
        Fetch labels, descriptions, and aliases from Wikidata based on the wikidata ID asynchronously.
        """
        if not wikidata_id:
            return None

        # API request to Wikidata to fetch labels, descriptions, and aliases
        url = (
            f"https://www.wikidata.org/w/api.php?"
            f"action=wbgetentities&ids={wikidata_id}"
            f"&props=labels|descriptions|aliases&languages=en|ar|he&format=json"
        )
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    result = await response.json()
                    entity_data = result.get("entities", {}).get(wikidata_id, {})

                    # Extract labels, descriptions, and aliases
                    labels_data = entity_data.get("labels", {})
                    descriptions_data = entity_data.get("descriptions", {})
                    aliases_data = entity_data.get("aliases", {})

                    # Prepare the data structure
                    data = {}
                    for lang in ['en', 'ar', 'he']:
                        data[lang] = {
                            'label': labels_data.get(lang, {}).get('value'),
                            'description': descriptions_data.get(lang, {}).get('value'),
                            'aliases': [alias['value'] for alias in aliases_data.get(lang, [])]
                        }

                    return data
        except aiohttp.ClientError as e:
            logger.error(f"Error fetching data for Wikidata ID {wikidata_id}: {e}")
            return None
        except ValueError as e:
            logger.error(f"Error parsing JSON response for Wikidata ID {wikidata_id}: {e}")
            return None

    async def extract_opencage_data(self):
        opencage_results = self.data.get("OpenCage", {}).get("results", [])
        opencage_data = []
        tasks = []

        for index, result in enumerate(opencage_results):
            try:
                annotations = result.get("annotations", {})
                bounds = result.get("bounds", {})
                components = result.get("components", {})
                geometry = result.get("geometry", {})
                wikidata_id = annotations.get("wikidata")

                # If there is a wikidata_id, create a task, otherwise use asyncio.sleep(0) as a placeholder
                if wikidata_id:
                    tasks.append(self.fetch_wikidata_aliases(wikidata_id))
                else:
                    tasks.append(asyncio.sleep(0))  # Use a placeholder coroutine
            except Exception as e:
                logger.error(f"Error processing OpenCage result at index {index}: {e}")
                tasks.append(asyncio.sleep(0))  # Placeholder coroutine for error cases

        # Fetch all aliases concurrently
        wikidata_aliases_results = await asyncio.gather(*tasks)

        for index, result in enumerate(opencage_results):
            try:
                annotations = result.get("annotations", {})
                bounds = result.get("bounds", {})
                components = result.get("components", {})
                geometry = result.get("geometry", {})
                wikidata_aliases = wikidata_aliases_results[index]

                # Handle missing fields gracefully
                def get_component(field):
                    return components.get(field) if field in components else None

                # Create boundingbox list
                northeast_lat = bounds.get("northeast", {}).get("lat")
                northeast_lon = bounds.get("northeast", {}).get("lon") or bounds.get("northeast", {}).get("lng")
                southwest_lat = bounds.get("southwest", {}).get("lat")
                southwest_lon = bounds.get("southwest", {}).get("lon") or bounds.get("southwest", {}).get("lng")
                boundingbox = list(map(str, filter(None, [
                    southwest_lat,  # South latitude
                    northeast_lat,  # North latitude
                    southwest_lon,  # West longitude
                    northeast_lon   # East longitude
                ])))

                opencage_data.append({
                    "index": index,
                    "lat": geometry.get("lat"),
                    "lon": geometry.get("lng"),  # Renamed 'lng' to 'lon'
                    "DMS_lat": annotations.get("DMS", {}).get("lat"),
                    "DMS_lon": annotations.get("DMS", {}).get("lng"),  # Renamed 'DMS_lng' to 'DMS_lon'
                    "OSM_url": annotations.get("OSM", {}).get("url"),
                    "wikidata": annotations.get("wikidata"),
                    "wikidata_aliases": wikidata_aliases,
                    "boundingbox": boundingbox,
                    "components": {
                        "_category": get_component("_category"),
                        "_normalized_city": get_component("_normalized_city"),
                        "_type": get_component("_type"),
                        "city": get_component("city"),
                        "continent": get_component("continent"),
                        "country": get_component("country"),
                        "country_code": get_component("country_code"),
                        "state": get_component("state"),
                        "state_district": get_component("state_district")
                    },
                    # Rename 'confidence' to 'importance' and divide by 10
                    "importance": result.get("confidence") / 10 if result.get("confidence") else None,
                })
            except Exception as e:
                logger.error(f"Error processing OpenCage result at index {index}: {e}")
                continue  # Skip this result and proceed to the next

        return opencage_data

    def extract_nominatim_data(self):
        nominatim_results = self.data.get("Nominatim", [])
        nominatim_data = []
        
        for index, result in enumerate(nominatim_results):
            try:
                nominatim_data.append({
                    "index": index,
                    "lat": result.get("lat"),
                    "lon": result.get("lon"),  # Changed 'lng' to 'lon' for consistency
                    "addresstype": result.get("addresstype"),
                    "name": result.get("name"),
                    "display_name": result.get("display_name"),
                    "boundingbox": result.get("boundingbox"),
                    "importance": result.get("importance")
                })
            except Exception as e:
                logger.error(f"Error processing Nominatim result at index {index}: {e}")
                continue  # Skip this result and proceed to the next
        
        return nominatim_data

    def extract_locationiq_data(self):
        locationiq_results = self.data.get("LocationIQ", [])
        locationiq_data = []
        
        for index, result in enumerate(locationiq_results):
            try:
                locationiq_data.append({
                    "index": index,
                    "lat": result.get("lat"),
                    "lon": result.get("lon"),  # Changed 'lng' to 'lon' for consistency
                    "boundingbox": result.get("boundingbox"),
                    "display_name": result.get("display_name"),
                    "type": result.get("type"),
                    "importance": result.get("importance"),
                    "class": result.get("class")
                })
            except Exception as e:
                logger.error(f"Error processing LocationIQ result at index {index}: {e}")
                continue  # Skip this result and proceed to the next
        
        return locationiq_data

    async def extract_all_data(self):
        extracted_data = {
            "OpenCage": await self.extract_opencage_data(),
            "Nominatim": self.extract_nominatim_data(),
            "LocationIQ": self.extract_locationiq_data()
        }

        # Convert the extracted data to a JSON string with UTF-8 encoding
        return json.dumps(extracted_data, indent=4, ensure_ascii=False)

# # Example usage
# def run_geocode_extractor(data):
#     extractor = GeocodeDataExtractor(data)
#     return asyncio.run(extractor.extract_all_data())
