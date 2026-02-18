import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

response = client.models.generate_content(
    model="models/gemini-flash-lite-latest",
    contents="Say hello in one word."
)

print(response.text)
