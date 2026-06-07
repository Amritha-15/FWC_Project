import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.environ.get("GROQ_API_KEY")
print(f"API Key set? {bool(api_key)}")

if not api_key:
    print("❌ GROQ_API_KEY not in .env")
    exit(1)

client = Groq(api_key=api_key)

# List available models
try:
    models = client.models.list()
    print("\n✅ Available Groq Models:")
    for model in models.data:
        print(f"  - {model.id}")
except Exception as e:
    print(f"❌ Cannot list models: {e}")
    exit(1)

# Try a simple API call
print("\n🧪 Testing simple API call...")
try:
    response = client.chat.completions.create(
        model="gemma-7b-it",  # Try this first (smallest)
        messages=[{"role": "user", "content": "Say hello"}],
        temperature=0.2,
        max_tokens=100
    )
    print(f"✅ API works! Response: {response.choices[0].message.content[:50]}")
except Exception as e:
    print(f"❌ API call failed: {e}")