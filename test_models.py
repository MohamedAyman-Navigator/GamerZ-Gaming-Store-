import google.generativeai as genai

# PASTE YOUR KEY HERE
genai.configure(api_key="PASTE YOUR API HERE")

print("Listing available models...")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
