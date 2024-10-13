import base64
from typing import Optional
from pydantic import BaseModel
import os
import openai
from dotenv import load_dotenv

from cost_calculator import CostCalculator

# Load environment variables from a .env file
load_dotenv()

# Set your OpenAI API key from the environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')

class OpenAIClient:
    """Helper class to interact with OpenAI API."""

    def __init__(self, model: str = "gpt-4o-2024-08-06", show_prices: bool = True):
        self.model = model
        self.show_prices = show_prices
        self.cost_calculator = CostCalculator(self.model)

    def _encode_image(self, image_path: str) -> str:
        """Encode an image from a file path to a base64 string."""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"Error encoding image: {e}")
            return None
        
    def _prepare_messages(self, system_message: str, user_message: str, image_path: Optional[str] = None):
        """Prepare messages to be sent to the API, with optional image encoding."""
        messages = [{"role": "system", "content": system_message}]
        
        # If an image path is provided, encode the image and create the image_url
        if image_path:
            base64_image = self._encode_image(image_path)
            if base64_image:
                user_content = [
                    {"type": "text", "text": user_message},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                ]
            else:
                user_content = user_message
        else:
            user_content = user_message
    
        messages.append({"role": "user", "content": user_content})
        return messages

    def _build_api_payload(self, messages, response_format: Optional[BaseModel] = None):
        """Build the payload for the OpenAI API request."""
        api_payload = {
            "model": self.model,
            "messages": messages,
            # "max_tokens": 300  # Default max tokens, can be customized as needed
        }
        if response_format:
            api_payload["response_format"] = response_format
        
        return api_payload

    def chat(self, system_message: str, user_message: str, image_path: Optional[str] = None, response_format: Optional[BaseModel] = None):
        """Main method to send a chat request to OpenAI with optional image input."""

        # Prepare messages
        messages = self._prepare_messages(system_message, user_message, image_path)

        # Calculate and display the prompt cost if required
        if self.show_prices:
            full_prompt = system_message + user_message
            has_image = image_path is not None
            prompt_cost = self.cost_calculator.calculate_prompt_cost(full_prompt, has_image=has_image)
            print(f"Prompt cost: ${prompt_cost:.6f}")

        # Build API payload
        api_payload = self._build_api_payload(messages, response_format)

        # Make API call and handle errors
        try:
            response = openai.beta.chat.completions.parse(**api_payload)
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return None

        # Calculate and display the completion cost if required
        if response and self.show_prices and response.choices:
            completion_text = response.choices[0].message.content
            completion_cost = self.cost_calculator.calculate_completion_cost(completion_text)
            print(f"Completion cost: ${completion_cost:.6f}")
        return response