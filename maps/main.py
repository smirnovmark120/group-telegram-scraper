import json
import asyncio

from geo_data_filter import GeoDataFilter
from geocode_data_extractor import GeocodeDataExtractor
from multi_geocoder import MultiGeocoder

from arabic_ner_client_hf import ArabicNERClientHF

# sentence = """
#     إسحق رابين، ولد في تل أبيب عام 1922، وكان رئيس وزراء دولة إسرائيل بين عامي 1974 و1977 ومرة ​​أخرى بين عامي 1992 و1995.
#     درس في جامعة القدس وكان ضابطا كبيرا في جيش الدفاع الإسرائيلي، الذي قاد النصر الإسرائيلي في حرب الأيام الستة عام 1967.
#     خلال فترة ولايته الثانية كرئيس للوزراء، وقع رابين اتفاقيات أوسلو مع ياسر عرفات، زعيم منظمة التحرير الفلسطينية، واتفاقية السلام مع الأردن في عام 1994.
#     في نوفمبر 1995، اغتيل رابين على يد ييجال عمير خلال مسيرة من أجل السلام في ميدان ملوك إسرائيل.
# """

# client = ArabicNERClientHF()
# response = client.get_locations_above_threshold(
#     sentence = sentence,
#     threshold = 0.75
# )
# print(f"Places mentioned in the message: {response}")

# # Initialize the geocoder
# geocoder = MultiGeocoder()

# # Main processing function
# async def process_places(response):
#     all_filtered_results = []
    
#     for place in response:  # assuming 'response' is a list of place names (NER output)
#         print(f"\nProcessing place: {place}")  # Debug: indicate current place being processed
        
#         # Get geocoding data for the place
#         all_results = await geocoder.get_all_coordinates(place)        
#         parsed_json_data = json.loads(all_results)
        
#         # Extract all relevant geocoding data
#         extractor = GeocodeDataExtractor(parsed_json_data)
#         all_data = await extractor.extract_all_data()
#         all_data = json.loads(all_data)
        
#         # Filter the geocoded data by importance
#         filter_obj = GeoDataFilter(all_data, importance_threshold=0.6)
#         filtered_results = filter_obj.get_coordinates_with_names()
        
#         # Ensure filtered_results is not None before extending the final list
#         if filtered_results:
#             # Add the NER word (place) to the result dictionary
#             filtered_results["ner_word"] = place  # Attach the NER word to each result
#             print(f"Appending filtered results with NER word: {filtered_results}")  # Debug
#             all_filtered_results.append(filtered_results)  # Append the entire dictionary
#         else:
#             print(f"No significant results found for: {place}")  # Debug: when no significant results
    
#     print(f"\nAll filtered results: {all_filtered_results}")  # Debug: print final filtered results
#     return all_filtered_results

# # Example usage:
# filtered_results = asyncio.run(process_places(response))

# # Final check and output: Ensure proper printing of the full dictionaries
# if filtered_results:
#     print("Final filtered results with coordinates and NER word:")
#     for result in filtered_results:
#         if isinstance(result, dict):
#             print(result)  # Print the entire dictionary correctly, including the NER word
#         else:
#             print(f"Unexpected result format: {result}")  # Debug if something unexpected comes
# else:
#     print("No filtered results with significant coordinates.")

geocoder = MultiGeocoder()
place = "Modiin maccabim reut"
all_results = asyncio.run(geocoder.get_all_coordinates(place))
# print(all_results)

parsed_json_data = json.loads(all_results)
extractor = GeocodeDataExtractor(parsed_json_data)
all_data = asyncio.run(extractor.extract_all_data())
print(all_data)

# all_data = json.loads(all_data)
# filter_obj = GeoDataFilter(all_data, importance_threshold=0.6)
# filtered_results = filter_obj.get_coordinates_with_names()

# print(filtered_results)