"""
Debug conversation memory to see extracted trip details
"""

import requests
import json

BASE_URL = "http://localhost:8080"

messages = []

# Turn 1
messages.append({"role": "user", "content": "I need travel insurance"})
response1 = requests.post(
    f"{BASE_URL}/v1/chat/completions",
    json={"model": "travelmate-ai", "messages": messages, "stream": False},
    timeout=30
).json()
messages.append({"role": "assistant", "content": response1['choices'][0]['message']['content']})

print("="*80)
print("TURN 1:")
print(f"User: {messages[-2]['content']}")
print(f"Assistant: {messages[-1]['content'][:150]}...")

# Turn 2 - via /ask endpoint to see full response
messages_turn2 = messages.copy()
messages_turn2.append({"role": "user", "content": "I'm going to Japan"})

print("\n" + "="*80)
print("TURN 2 (via /ask to see full response):")
print(f"User: {messages_turn2[-1]['content']}")

# Build context for /ask
context = {
    "conversation_history": messages  # All previous messages
}

ask_response = requests.post(
    f"{BASE_URL}/ask",
    json={
        "question": "I'm going to Japan",
        "context": context
    },
    timeout=30
).json()

print(f"\n📊 EXTRACTED TRIP DETAILS:")
print(json.dumps(ask_response.get("trip_details", {}), indent=2))

print(f"\n💬 Assistant Answer: {ask_response.get('answer', '')[:150]}...")

messages.append({"role": "user", "content": "I'm going to Japan"})
messages.append({"role": "assistant", "content": ask_response.get('answer', '')})

# Turn 3
messages_turn3 = messages.copy()
messages_turn3.append({"role": "user", "content": "December for 9 days, I'm 31"})

print("\n" + "="*80)
print("TURN 3 (via /ask to see full response):")
print(f"User: {messages_turn3[-1]['content']}")

# Build context including extracted trip details from Turn 2
context_turn3 = {
    "conversation_history": messages,
    "extracted_trip_details": ask_response.get("trip_details", {})  # Pass extracted details
}

ask_response3 = requests.post(
    f"{BASE_URL}/ask",
    json={
        "question": "December for 9 days, I'm 31",
        "context": context_turn3
    },
    timeout=60
).json()

print(f"\n📊 EXTRACTED TRIP DETAILS:")
print(json.dumps(ask_response3.get("trip_details", {}), indent=2))

print(f"\n💬 Assistant Answer: {ask_response3.get('answer', '')[:300]}...")

print("\n" + "="*80)
print("ANALYSIS:")
print("="*80)

trip_details = ask_response3.get("trip_details", {})
print(f"Destination: {trip_details.get('destination_country', 'NOT EXTRACTED')}")
print(f"Dates: {trip_details.get('departure_date', 'NOT EXTRACTED')} to {trip_details.get('return_date', 'NOT EXTRACTED')}")
print(f"Duration: {trip_details.get('trip_duration_days', 'NOT EXTRACTED')} days")
print(f"Travelers: {len(trip_details.get('travelers', []))} people")

if trip_details.get('destination_country') == 'Japan':
    print("\n✅ Conversation history WORKING - Japan extracted from Turn 2!")
else:
    print("\n❌ Conversation history NOT WORKING - Japan lost from Turn 2")

