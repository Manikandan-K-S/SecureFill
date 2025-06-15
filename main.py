import socket
import threading
import json
import time

# Import the form-filling engine we built
from modelEngine import parser as form_filler_engine

# --- Configuration for Communication ---
ORCHESTRATOR_PORT = 6001 
HOST_PORT = 6000
HOST_IP = '127.0.0.1'

# Global variable to store the received data from the extension
received_html_data = None
data_received_event = threading.Event()

def start_result_listener():
    """Waits for host.py to connect and send the scanned HTML data."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST_IP, ORCHESTRATOR_PORT))
        s.listen()
        print(f"[Orchestrator] Listening for scan results on port {ORCHESTRATOR_PORT}...")
        conn, addr = s.accept()
        with conn:
            print(f"[Orchestrator] Host.py connected from {addr}")
            data_chunks = []
            while True:
                chunk = conn.recv(4096)
                if not chunk: break
                data_chunks.append(chunk)
            
            raw_data = b''.join(data_chunks).decode('utf-8')
            global received_html_data
            received_html_data = json.loads(raw_data)
            
            print(f"[Orchestrator] Successfully received {len(received_html_data)} HTML fields.")
            data_received_event.set()

def trigger_scan_in_extension():
    """Connects to host.py and sends the 'scan' command."""
    print("[Orchestrator] Sending 'scan' command to host.py...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST_IP, HOST_PORT))
            s.sendall(json.dumps({"command": "scan"}).encode('utf-8'))
            print("[Orchestrator] 'scan' command sent successfully.")
        except ConnectionRefusedError:
            print(f"[Orchestrator] Error: Connection to host.py on port {HOST_PORT} was refused.")
            return False
    return True

def send_action_plan_to_host(plan: list):
    """Connects to host.py to send the final action plan for execution."""
    print("[Orchestrator] Sending final action plan to host.py for execution...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST_IP, HOST_PORT))
            command = {"command": "execute_plan", "payload": plan}
            s.sendall(json.dumps(command).encode('utf-8'))
            print("[Orchestrator] Final action plan sent successfully.")
        except ConnectionRefusedError:
            print(f"[Orchestrator] Error: Could not send action plan to host.py.")

def cleanup_action_plan(plan: list) -> list:
    """Cleans the AI-generated action plan to remove common errors."""
    if not isinstance(plan, list): return []
    cleaned_plan, seen_selectors = [], set()
    for action in plan:
        if not isinstance(action, dict) or not all(k in action for k in ["selector", "action_type", "value"]):
            continue
        selector = action.get("selector")
        if selector in seen_selectors:
            continue
        if action.get("action_type") == "FILL_TEXT" and isinstance(action.get("value"), bool):
            continue
        cleaned_plan.append(action)
        seen_selectors.add(selector)
    return cleaned_plan

# --- Main Application Logic ---
if __name__ == "__main__":
    print("--- SecureFill Orchestrator Engine ---")
    
    print("-" * 50)
    user_prompt = input("Enter a fill instruction (e.g., 'Use my work info') or press Enter for default: ")
    print("-" * 50)
    
    listener_thread = threading.Thread(target=start_result_listener)
    listener_thread.daemon = True
    listener_thread.start()

    if not trigger_scan_in_extension():
        exit()

    print("[Orchestrator] Waiting for HTML data from the extension...")
    scan_successful = data_received_event.wait(timeout=30)

    if not scan_successful or not received_html_data:
        print("[Orchestrator] Timed out or failed to receive data from the extension.")
        exit()

    html_fields = received_html_data

    # --- NEW LOGGING STEP 1: Show the incoming HTML ---
    print("\n--- Raw HTML Snippets Received ---")
    print(json.dumps(html_fields, indent=2))
    print("------------------------------------")
    
    config = form_filler_engine.load_config()
    llm = form_filler_engine.initialize_llm(config)
    vectorstore = form_filler_engine.initialize_vectorstore()

    if not all([config, llm, vectorstore]):
        print("\nExiting due to parser engine initialization errors.")
        exit()
        
    analyze_chain = form_filler_engine.analysis_prompt | llm | form_filler_engine.StrOutputParser()
    action_plan_chain = form_filler_engine.action_plan_prompt | llm | form_filler_engine.StrOutputParser()

    start_time = time.time()
    
    analysis_plan = form_filler_engine.analyze_form_and_create_search_plan(
        analyze_chain, html_fields, user_prompt
    )
    
    if analysis_plan:
        search_results = form_filler_engine.search_vector_db(
            vectorstore, analysis_plan, top_k=2
        )
        raw_action_plan = form_filler_engine.generate_action_plan(
            action_plan_chain, search_results, user_prompt
        )
        
        # --- NEW LOGGING STEP 2: Show the raw plan before cleanup ---
        print("\n--- Raw AI-Generated Action Plan (Before Cleanup) ---")
        print(json.dumps(raw_action_plan, indent=2))
        print("----------------------------------------------------")

        print("\n--- Running Cleanup Function ---")
        final_action_plan = cleanup_action_plan(raw_action_plan)
        
        end_time = time.time()
        print(f"\n--- Total AI Processing Time: {end_time - start_time:.2f} seconds ---")

        print("\n--- ✅ Final Cleaned Action Plan ---")
        print(json.dumps(final_action_plan, indent=2))

        if final_action_plan:
            send_action_plan_to_host(final_action_plan)

    else:
        print("\nExecution stopped. The AI failed to create an analysis plan.")
