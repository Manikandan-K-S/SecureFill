# host.py - The "Always-On" Listener Service

import sys
import json
import struct
import logging
import socket
import threading

# --- Setup Logging ---
log_file_path = 'host_log.log'
logging.basicConfig(filename=log_file_path, level=logging.INFO, format='%(asctime)s - %(message)s')

# --- Native Messaging Functions (to talk to browser) ---
def send_message_to_extension(message_content):
    encoded_content = json.dumps(message_content).encode('utf-8')
    encoded_length = struct.pack('@I', len(encoded_content))
    logging.info(f"Sending message to extension: {message_content}")
    sys.stdout.buffer.write(encoded_length)
    sys.stdout.buffer.write(encoded_content)
    sys.stdout.buffer.flush()

def read_message_from_extension():
    raw_length = sys.stdin.buffer.read(4)
    if not raw_length:
        return None
    message_length = struct.unpack('@I', raw_length)[0]
    message = sys.stdin.buffer.read(message_length).decode('utf-8')
    return json.loads(message)

# --- Local Trigger Server (to listen for our trigger.py) ---
def start_trigger_listener():
    # This server runs on a background thread to listen for local commands
    host, port = '127.0.0.1', 6000 # A private port for our app
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        while True:
            conn, addr = s.accept()
            with conn:
                data = conn.recv(1024)
                if data.decode('utf-8') == 'scan':
                    logging.info("Received 'scan' command from local trigger.")
                    send_message_to_extension({"command": "scan_page"})

# --- Main Logic ---
logging.info("--- Host Service Started by Browser ---")

# Start the trigger listener in the background
trigger_thread = threading.Thread(target=start_trigger_listener)
trigger_thread.daemon = True
trigger_thread.start()

# Main thread loop to listen for messages from the browser
try:
    while True:
        message = read_message_from_extension()
        if message:
            logging.info(f"Received data from extension: {json.dumps(message, indent=2)}")
            # In a real app, you would save this data or pass it on.
        else:
            logging.info("Browser closed the connection. Exiting.")
            break
except Exception as e:
    logging.exception("An error occurred in the main host loop.")