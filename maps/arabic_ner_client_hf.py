import os
from dotenv import load_dotenv
import requests

class ArabicNERClientHF:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()

        # Fetch the Hugging Face API URL and key from user environment variables
        self.api_url = os.getenv('HUGGINGFACE_API_URL')
        self.api_key = os.getenv('HUGGINGFACE_API_KEY')

        # Set the headers for the requests
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def query(self, sentence):
        # Prepare the payload with the given sentence
        payload = {
            "inputs": sentence,
            "parameters": {
                "aggregation_strategy": "simple"
            }
        }
        # Send a POST request to the Hugging Face API
        response = requests.post(self.api_url, headers=self.headers, json=payload)

        # Try to parse JSON response
        try:
            result = response.json()
            return result
        except ValueError:
            # If JSON parsing fails, print the error message and raw response
            print("Failed to parse JSON response.")
            print(f"Raw response content: {response.text}")  # Print raw response content
            return None

    def get_locations_above_threshold(self, sentence, threshold=0.75):
        """
        This function extracts all locations (LOC) from the model's output
        with a score higher than the specified threshold (default 75%).
        """
        # Get the response from the API
        result = self.query(sentence)

        if not result or not isinstance(result, list):
            print(f"Unexpected response format: {result}")
            return []

        # Extract the entities
        locations = []

        # Ensure we're working with a list of dictionaries
        for entity in result:
            if isinstance(entity, dict) and 'entity_group' in entity and 'score' in entity:
                if entity['entity_group'] == 'LOC' and entity['score'] > threshold:
                    # Append the location to the list if score is greater than the threshold
                    locations.append(entity['word'])
            else:
                print(f"Unexpected entity format: {entity}")

        return locations

# # Example usage
# sentence = "إمارة أبوظبي هي إحدى إمارات دولة الإمارات العربية المتحدة السبع"

# client = ArabicNERClientHF()
# response = client.get_locations_above_threshold(
#     sentence=sentence,
#     threshold=0.75
# )
# print(f"Places mentioned in the message: {response}")
