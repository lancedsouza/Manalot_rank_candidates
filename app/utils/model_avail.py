import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("Fetching available models...")
try:
    for model in client.models.list():
        # Look for the flash models
        if "flash" in model.name.lower():
            print(f"  - {model.name}")
except Exception as e:
    print(f"Error fetching models: {e}")
