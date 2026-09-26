import os
from google import genai
from google.genai import types

client = genai.Client(api_key="AIzaSyA_FAKE_KEY_FOR_TESTING_PURPOSES_ONLY")
try:
    for m in client.models.list():
        if "generateContent" in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"ERROR: {e}")
