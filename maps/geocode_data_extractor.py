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

                    labels_data = entity_data.get("labels", {})
                    descriptions_data = entity_data.get("descriptions", {})
                    aliases_data = entity_data.get("aliases", {})

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
        opencage_data = self.data.get("OpenCage", {})
        
        # Check for errors or did not find cases
        if opencage_data.get("status", {}).get("code") != 200:
            logger.error(f"OpenCage error: {opencage_data.get('status', {}).get('message', 'Unknown error')}")
            return []

        if opencage_data.get("total_results", 0) == 0:
            logger.warning("OpenCage did not find the place")
            return [{"message": "did not find place"}]

        opencage_results = opencage_data.get("results", [])
        extracted_data = []
        tasks = []

        for index, result in enumerate(opencage_results):
            try:
                annotations = result.get("annotations", {})
                bounds = result.get("bounds", {})
                components = result.get("components", {})
                geometry = result.get("geometry", {})
                wikidata_id = annotations.get("wikidata")

                if wikidata_id:
                    tasks.append(self.fetch_wikidata_aliases(wikidata_id))
                else:
                    tasks.append(asyncio.sleep(0))  # Placeholder
            except Exception as e:
                logger.error(f"Error processing OpenCage result at index {index}: {e}")
                tasks.append(asyncio.sleep(0))  # Placeholder

        wikidata_aliases_results = await asyncio.gather(*tasks)

        for index, result in enumerate(opencage_results):
            try:
                annotations = result.get("annotations", {})
                bounds = result.get("bounds", {})
                components = result.get("components", {})
                geometry = result.get("geometry", {})
                wikidata_aliases = wikidata_aliases_results[index]

                def get_component(field):
                    return components.get(field) if field in components else None

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

                extracted_data.append({
                    "index": index,
                    "lat": geometry.get("lat"),
                    "lon": geometry.get("lng"),
                    "DMS_lat": annotations.get("DMS", {}).get("lat"),
                    "DMS_lon": annotations.get("DMS", {}).get("lng"),
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
                    "importance": result.get("confidence") / 10 if result.get("confidence") else None,
                })
            except Exception as e:
                logger.error(f"Error processing OpenCage result at index {index}: {e}")
                continue

        return extracted_data

    def extract_nominatim_data(self):
        nominatim_results = self.data.get("Nominatim", [])
        
        if not nominatim_results:
            logger.warning("Nominatim did not find the place")
            return [{"message": "did not find place"}]

        nominatim_data = []
        for index, result in enumerate(nominatim_results):
            try:
                nominatim_data.append({
                    "index": index,
                    "lat": result.get("lat"),
                    "lon": result.get("lon"),
                    "addresstype": result.get("addresstype"),
                    "name": result.get("name"),
                    "display_name": result.get("display_name"),
                    "boundingbox": result.get("boundingbox"),
                    "importance": result.get("importance")
                })
            except Exception as e:
                logger.error(f"Error processing Nominatim result at index {index}: {e}")
                continue
        
        return nominatim_data

    def extract_locationiq_data(self):
        locationiq_results = self.data.get("LocationIQ", {})

        if not isinstance(locationiq_results, list) or not locationiq_results:
            logger.warning("LocationIQ did not find the place")
            return [{"message": "did not find place"}]

        if isinstance(locationiq_results, dict) and "error" in locationiq_results:
            logger.error(f"LocationIQ error: {locationiq_results['error']}")
            return []

        locationiq_data = []
        for index, result in enumerate(locationiq_results):
            try:
                if isinstance(result, dict):
                    locationiq_data.append({
                        "index": index,
                        "lat": result.get("lat"),
                        "lon": result.get("lon"),
                        "boundingbox": result.get("boundingbox"),
                        "display_name": result.get("display_name"),
                        "type": result.get("type"),
                        "importance": result.get("importance"),
                        "class": result.get("class")
                    })
            except Exception as e:
                logger.error(f"Error processing LocationIQ result at index {index}: {e}")
                continue
        
        return locationiq_data

    async def extract_all_data(self):
        extracted_data = {
            "OpenCage": await self.extract_opencage_data(),
            "Nominatim": self.extract_nominatim_data(),
            "LocationIQ": self.extract_locationiq_data()
        }

        return json.dumps(extracted_data, indent=4, ensure_ascii=False)

# # Example usage
# def run_geocode_extractor(data):
#     extractor = GeocodeDataExtractor(data)
#     return asyncio.run(extractor.extract_all_data())
