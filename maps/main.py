import json
import asyncio

from geo_data_filter import GeoDataFilter
from geocode_data_extractor import GeocodeDataExtractor
from multi_geocoder import MultiGeocoder

geocoder = MultiGeocoder()
place = "Hebron"
all_results = asyncio.run(geocoder.get_all_coordinates(place))

parsed_json_data = json.loads(all_results)
extractor = GeocodeDataExtractor(parsed_json_data)
all_data = asyncio.run(extractor.extract_all_data())

all_data = json.loads(all_data)
filter_obj = GeoDataFilter(all_data, importance_threshold=0.6)
filtered_results = filter_obj.get_coordinates_with_names()

print(filtered_results)