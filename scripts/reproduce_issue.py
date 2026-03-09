from core.ymove import parse_and_find_videos

text_with_html = """
1️⃣ <b>Push-Up Variations</b>
📌 Mushaklar: Ko'krak
🔁 3 set x 12
"""

print("Testing with HTML tags:")
results = parse_and_find_videos(text_with_html)
print(f"Results: {results}")

text_plain = """
1. Push-Up Variations - 3x12
"""
print("\nTesting plain text:")
results2 = parse_and_find_videos(text_plain)
print(f"Results: {results2}")
