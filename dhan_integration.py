import websocket
import json
import threading
import time

# Define the WebSocket URL for Dhan API
Dhan_API_URL = "wss://ws.dhan.co.in/live"

# Function to handle incoming messages from the WebSocket
def on_message(ws, message):
    data = json.loads(message)
    # Handle Nifty 50 and Bank Nifty data
    if data['s'] == 'NIFTY50':
        print(f"Nifty 50: {data['p']}")
    elif data['s'] == 'BANKNIFTY':
        print(f"Bank Nifty: {data['p']}")

# Function to handle WebSocket error events
def on_error(ws, error):
    print(f"Error: {error}")

# Function to handle WebSocket close events
def on_close(ws):
    print("### closed ###")

# Function to handle WebSocket open events
def on_open(ws):
    print("Opened connection, subscribing to Nifty 50 and Bank Nifty.")
    # Subscribe to Nifty 50 and Bank Nifty
    subscribe_message = {
        "type": "subscribe",
        "symbols": ["NIFTY50", "BANKNIFTY"]
    }
    ws.send(json.dumps(subscribe_message))

# Function to run the WebSocket connection
def run():
    ws = websocket.WebSocketApp(Dhan_API_URL,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()

# Keep the WebSocket connection alive with error handling
if __name__ == "__main__":
    while True:
        try:
            run()
        except Exception as e:
            print(f"Exception: {e}, reconnecting...")
            time.sleep(5)  # Wait before reconnecting\n