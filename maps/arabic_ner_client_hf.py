import os
import time  # Import time module to use sleep for retry
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

    def query(self, sentence, max_retries=3):
        """
        Send a POST request to the Hugging Face API, with retry mechanism for 503 errors.
        """
        payload = {
            "inputs": sentence,
            "parameters": {
                "aggregation_strategy": "simple"
            }
        }

        retries = 0
        while retries < max_retries:
            response = requests.post(self.api_url, headers=self.headers, json=payload)

            # Check for 503 Service Unavailable error
            if response.status_code == 503:
                print(f"Service unavailable (503). Retrying after 5 seconds... ({retries + 1}/{max_retries})")
                time.sleep(5)  # Wait for 5 seconds before retrying
                retries += 1
            else:
                # If no 503 error, try to parse the response
                try:
                    result = response.json()
                    return result
                except ValueError:
                    print("Failed to parse JSON response.")
                    print(f"Raw response content: {response.text}")
                    return None
        
        # If retries exceeded and still no success
        print("Max retries exceeded. Service may still be unavailable.")
        return None

    def get_locations_above_threshold(self, sentence, threshold=0.75):
        """
        This function extracts all locations (LOC) from the model's output
        with a score higher than the specified threshold (default 75%).
        """
        result = self.query(sentence)

        if not result or not isinstance(result, list):
            print(f"Unexpected response format: {result}")
            return []

        locations = []

        for entity in result:
            if isinstance(entity, dict) and 'entity_group' in entity and 'score' in entity:
                if entity['entity_group'] == 'LOC' and entity['score'] > threshold:
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
