import sys
import json
import struct
import logging
import socket
import threading

# --- Configuration ---
ORCHESTRATOR_IP = '127.0.0.1'
ORCHESTRATOR_PORT = 6001 
HOST_PORT = 6000

# --- Setup Logging ---
log_file_path = 'host_log.log'
logging.basicConfig(
    filename=log_file_path, 
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- Native Messaging (Browser Communication) ---
def send_message_to_extension(message_content):
    """Encodes and sends a message TO the browser extension via stdout."""
    try:
        encoded_content = json.dumps(message_content).encode('utf-8')
        encoded_length = struct.pack('@I', len(encoded_content))
        logging.info(f"To Extension >> Relaying command: {message_content.get('command')}")
        sys.stdout.buffer.write(encoded_length)
        sys.stdout.buffer.write(encoded_content)
        sys.stdout.buffer.flush()
    except (IOError, BrokenPipeError) as e:
        logging.warning(f"Pipe to browser broken: {e}")

def read_message_from_extension():
    """Reads and decodes a message FROM the browser extension via stdin."""
    try:
        raw_length = sys.stdin.buffer.read(4)
        if not raw_length: return None
        message_length = struct.unpack('@I', raw_length)[0]
        message_content = sys.stdin.buffer.read(message_length).decode('utf-8')
        return json.loads(message_content)
    except Exception as e:
        logging.warning(f"Could not read from browser: {e}")
        return None

# --- Orchestrator Communication ---
def send_data_to_orchestrator(data):
    """Connects to the main.py orchestrator and sends it the scanned HTML data."""
    logging.info(f"To Orchestrator >> Sending {len(data)} HTML fields...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((ORCHESTRATOR_IP, ORCHESTRATOR_PORT))
            s.sendall(json.dumps(data).encode('utf-8'))
            logging.info("To Orchestrator >> Data sent successfully.")
        except ConnectionRefusedError:
            logging.error(f"Could not connect to Orchestrator on port {ORCHESTRATOR_PORT}. Is main.py running?")

def start_command_listener():
    """
    Listens for commands from the main.py orchestrator. Handles both 'scan' and 'execute_plan'.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('127.0.0.1', HOST_PORT))
        s.listen()
        logging.info(f"Listening for commands from Orchestrator on port {HOST_PORT}")
        while True:
            conn, addr = s.accept()
            with conn:
                data_chunks = []
                while True:
                    chunk = conn.recv(4096)
                    if not chunk: break
                    data_chunks.append(chunk)
                
                raw_data = b''.join(data_chunks).decode('utf-8')
                if not raw_data: continue

                try:
                    request = json.loads(raw_data)
                    command = request.get("command")
                    logging.info(f"From Orchestrator << Received command: '{command}'")

                    if command == 'scan':
                        send_message_to_extension({"command": "scan_page"})
                    
                    elif command == 'execute_plan':
                        plan = request.get("payload", [])
                        send_message_to_extension({"command": "execute_action_plan", "plan": plan})
                
                except json.JSONDecodeError:
                    logging.error(f"Received non-JSON command from orchestrator: {raw_data}")


# --- Main Host Logic ---
def main():
    logging.info("--- Host Messenger Service Started by Browser ---")
    
    command_thread = threading.Thread(target=start_command_listener)
    command_thread.daemon = True
    command_thread.start()
    
    while True:
        message = read_message_from_extension()
        if message:
            action = message.get("action")
            logging.info(f"From Extension << Received action: '{action}'")
            
            if action == "contextual_scan_result":
                html_data = message.get("data", [])
                send_data_to_orchestrator(html_data)
        else:
            logging.warning("Browser closed the connection. Exiting host script.")
            break

if __name__ == "__main__":
    main()
