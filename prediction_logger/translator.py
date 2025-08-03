import openai
import logging
import os

class Translator:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY env variable or pass to Translator.")
        openai.api_key = self.api_key

    def summarize_tensor_output(self, tensor_output, context=None):
        prompt = f"Summarize the following tensor model output for a trading forecast. Output: {tensor_output}."
        if context:
            prompt += f" Context: {context}"
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=128,
                temperature=0.2,
            )
            summary = response.choices[0].message["content"].strip()
            return summary
        except Exception as e:
            logging.error(f"OpenAI API error: {e}")
            return None
