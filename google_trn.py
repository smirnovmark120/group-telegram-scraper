import os
import json
from dotenv import load_dotenv
from google.cloud import translate_v3 as translate
from typing import Optional, Dict

class TranslationService:
    def __init__(self, source_lang: str, target_lang: str):
        """
        Initialize the TranslationService.

        :param source_lang: The source language code (e.g., 'en' for English)
        :param target_lang: The target language code (e.g., 'es' for Spanish)
        """
        print("Loading environment variables...")
        load_dotenv()

        # Set up Google Cloud credentials
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        print(f"Using credentials from: {credentials_path}")

        # Load the project ID from the JSON credentials file
        try:
            with open(credentials_path, 'r') as f:
                credentials_data = json.load(f)
                self.project_id = credentials_data.get('project_id')
                print(f"Loaded project ID: {self.project_id}")
        except Exception as e:
            print(f"Error loading credentials file: {e}")
            raise

        # Initialize TranslationServiceClient for v3 API
        try:
            self.client = translate.TranslationServiceClient()
            print("TranslationServiceClient initialized successfully.")
        except Exception as e:
            print(f"Error initializing TranslationServiceClient: {e}")
            raise

        # Set language codes
        self.source_lang = source_lang
        self.target_lang = target_lang
        print(f"Source language: {self.source_lang}, Target language: {self.target_lang}")

    def translate(self, text: str) -> Optional[str]:
        """
        Translate the given text from source language to target language.

        :param text: The text to translate
        :return: The translated text, or None if translation fails
        """
        if not text:
            print("No text provided for translation.")
            return None

        parent = f"projects/{self.project_id}/locations/global"

        try:
            response = self.client.translate_text(
                parent=parent,
                contents=[text],
                source_language_code=self.source_lang,
                target_language_code=self.target_lang
            )
            # Return the translated text from the response
            translated_text = response.translations[0].translated_text
            return translated_text
        except Exception as e:
            print(f"Translation error: {e}")
            return None

    def change_source_language(self, new_source_lang: str) -> None:
        """
        Change the source language.

        :param new_source_lang: The new source language code
        """
        self.source_lang = new_source_lang
        print(f"Source language changed to: {self.source_lang}")

    def change_target_language(self, new_target_lang: str) -> None:
        """
        Change the target language.

        :param new_target_lang: The new target language code
        """
        self.target_lang = new_target_lang
        print(f"Target language changed to: {self.target_lang}")

# Example usage
if __name__ == "__main__":
    try:
        # Create a TranslationService instance
        translator = TranslationService(source_lang="en", target_lang="es")

        # Translate a sentence
        sentence = "Hello, how are you?"
        translated = translator.translate(sentence)

        if translated:
            print(f"Original: {sentence}")
            print(f"Translated: {translated}")
        else:
            print("Translation failed.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
