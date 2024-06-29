import json
message = {'event': 'data', 'data': '{"key": "https://www.youtube.com/shorts/AJtTZpBmIUY_tiny"}'}
# Assuming message['data'] is your JSON string
data = json.loads(message['data'])  # Parse the JSON string into a Python dictionary

# Check if 'data' contains exactly {'key': 'characters of key'}
if 'key' in data and isinstance(data['key'], str):
    # The message is in the desired format
    print("Message is in the correct format.")
else:
    # The message is not in the desired format
    print("Message is not in the correct format.")