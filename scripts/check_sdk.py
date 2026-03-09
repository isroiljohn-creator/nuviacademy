from google import genai
from google.genai import types

print("DIR of GenerateContentConfig:")
print(dir(types.GenerateContentConfig))
print("\nType Hints:")
try:
    print(types.GenerateContentConfig.__annotations__)
except:
    print("No annotations")
