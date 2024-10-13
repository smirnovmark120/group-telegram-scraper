import json
import tiktoken

class TokenCounter:
    def __init__(self, default_encoding: str = "o200k_base"):
        """
        Initialize the TokenCounter by loading model-encoding data from a local file.
        
        :param default_encoding: The default encoding to use if no closest match is found. Defaults to "o200k_base".
        """
        # Load the model encoding data
        self.model_encoding_map = {
            "gpt-4o": "o200k_base",
            "gpt-4o-mini": "o200k_base",
            "gpt-4-turbo": "cl100k_base",
            "gpt-4": "cl100k_base",
            "gpt-3.5-turbo": "cl100k_base",
            "text-embedding-ada-002": "cl100k_base",
            "text-embedding-3-small": "cl100k_base",
            "text-embedding-3-large": "cl100k_base",
            "Codex": "p50k_base",
            "text-davinci-002": "p50k_base",
            "text-davinci-003": "p50k_base",
            "davinci": "r50k_base"
        }

        self.default_encoding = default_encoding  # Set the default encoding to use if no match is found

    def num_tokens_from_string(self, string: str, model_name: str) -> int:
        """
        Returns the number of tokens in a text string for a specified model.
        
        :param string: The input text.
        :param model_name: The name of the model.
        :return: The number of tokens in the text.
        """
        # Try to get the exact model name first
        encoding_name = self.model_encoding_map.get(model_name)

        # If not found, check for partial matches
        if not encoding_name:
            matching_model = self._find_closest_model(model_name)
            if matching_model:
                encoding_name = self.model_encoding_map[matching_model]
                print(f"Using closest match for encoding: '{matching_model}' for input model '{model_name}'")
            else:
                # Default to "o200k_base" if no closest match is found
                encoding_name = self.default_encoding
                print(f"No close match found. Using default encoding: '{self.default_encoding}' for input model '{model_name}'")

        # Get encoding based on the encoding name
        encoding = tiktoken.get_encoding(encoding_name)
        
        # Count the tokens
        num_tokens = len(encoding.encode(string))
        return num_tokens

    def _find_closest_model(self, input_model: str) -> str:
        """
        Find the closest matching model name in the encoding map using substring matching.
        
        :param input_model: The input model name.
        :return: The closest matching model name or None if no match is found.
        """
        for model in self.model_encoding_map:
            if model in input_model:
                return model
        return None