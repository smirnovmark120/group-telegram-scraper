import requests
from token_counter import TokenCounter

class CostCalculator:
    def __init__(self, model_name: str):
        """
        Initialize the cost calculator by fetching pricing data from the URL, setting up the token counter, 
        and resolving the closest match for encoding, if needed. Pricing is resolved directly if available.

        :param model_name: The name of the model to use for both encoding and pricing.
        :param pricing_url: URL to fetch the pricing information.
        """
        self.token_counter = TokenCounter()
        
        # Fixed cost per image model used (gpt-4o)
        self.IMAGE_COST_PER_MODEL = 0.0021  

        # URL to the updated model pricing and context window data
        pricing_url = "https://raw.githubusercontent.com/BerriAI/litellm/refs/heads/main/model_prices_and_context_window.json"

        # Fetch the pricing data from the URL
        response = requests.get(pricing_url)
        if response.status_code == 200:
            self.pricing_data = response.json()
        else:
            raise ValueError(f"Failed to fetch pricing data. Status code: {response.status_code}")

        # Resolve and store the closest match for the encoding if necessary
        self.model_name = model_name
        self.encoding_model_name = self._resolve_encoding_model(model_name)
        print(f"Resolved model for encoding: '{self.encoding_model_name}'")

        # Use the exact model for pricing if found
        self.pricing_model_name = self._resolve_pricing_model(model_name)
        print(f"Using pricing model: '{self.pricing_model_name}'")

    def _resolve_encoding_model(self, model_name: str) -> str:
        """
        Resolve the closest matching model name for encoding using the TokenCounter.

        :param model_name: The original model name.
        :return: The resolved encoding model name (closest match).
        """
        # First, try to resolve the model in the TokenCounter (encoding map)
        encoding_model = self.token_counter._find_closest_model(model_name)
        if encoding_model:
            print(f"Using closest match for encoding: '{encoding_model}' for input model '{model_name}'")
            return encoding_model
        else:
            raise ValueError(f"No encoding found for model '{model_name}'.")

    def _resolve_pricing_model(self, model_name: str) -> str:
        """
        Resolve the pricing model by checking if the exact model exists in the pricing data.

        :param model_name: The original model name.
        :return: The exact pricing model name, or a closest match if necessary.
        """
        # If exact model name exists in pricing data, use it
        if model_name in self.pricing_data:
            return model_name
        else:
            # Try partial match for pricing if the exact model is not found
            pricing_model = self._find_closest_pricing_model(model_name)
            if pricing_model:
                print(f"Using closest match for pricing: '{pricing_model}' for input model '{model_name}'")
                return pricing_model
            else:
                raise ValueError(f"No pricing found for model '{model_name}'.")

    def calculate_prompt_cost(self, text_prompt: str, has_image: bool = False) -> float:
        """
        Calculate the cost for the given text prompt and optionally add the cost of using an image model.
        
        :param text_prompt: The text prompt to be tokenized and have its cost calculated.
        :param has_image: A boolean indicating if an image model is used (True if used, False otherwise).
        :return: The total calculated cost for the text prompt including image cost if applicable.
        """
        # Get the number of tokens in the text prompt using the resolved encoding model
        num_tokens = self.token_counter.num_tokens_from_string(text_prompt, self.encoding_model_name)
        
        # Get the cost per token for the text input
        input_cost_per_token = self.pricing_data[self.pricing_model_name]['input_cost_per_token']

        # Calculate the total cost for the text prompt
        text_prompt_cost = num_tokens * input_cost_per_token

        # Add image cost if an image model is used
        image_cost = self.IMAGE_COST_PER_MODEL if has_image else 0.0

        # Return the total cost (text prompt cost + image cost if applicable)
        return text_prompt_cost + image_cost

    def calculate_completion_cost(self, text_completion: str) -> float:
        """
        Calculate the cost for the given text completion based on the model's pricing.

        :param text_completion: The text completion to be tokenized and cost calculated.
        :return: The calculated cost for the completion.
        """
        # Get the number of tokens in the completion using the resolved encoding model
        num_tokens = self.token_counter.num_tokens_from_string(text_completion, self.encoding_model_name)
        
        # Get the cost per token for the completion (output)
        output_cost_per_token = self.pricing_data[self.pricing_model_name]['output_cost_per_token']

        # Calculate total cost based on the number of tokens
        completion_cost = num_tokens * output_cost_per_token
        return completion_cost

    def _find_closest_pricing_model(self, input_model: str) -> str:
        """
        Find the closest matching model name in the pricing data using substring matching.
        
        :param input_model: The input model name.
        :return: The closest matching pricing model name or None if no match is found.
        """
        for model in self.pricing_data:
            if model in input_model:
                return model
        return None