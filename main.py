import socket
import threading
import json
import time
import sys
import customtkinter as ctk # For the UI

# Import the form-filling engine we built
from modelEngine import parser as form_filler_engine

# --- Configuration ---
HOST_IP = '127.0.0.1'
ORCHESTRATOR_PORT = 6001 
HOST_PORT = 6000
process_lock = threading.Lock()


# --- UI Application Class (No changes needed here) ---
class UIApp(ctk.CTk):
    def __init__(self, prompt_callback):
        super().__init__()
        self.prompt_callback = prompt_callback
        self.title("SecureFill Assistant")
        self.attributes('-topmost', True)
        self.geometry(self.center_window(450, 280))
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(pady=20, padx=20, fill="both", expand=True)
        self.status_label = ctk.CTkLabel(main_frame, text="What would you like to do?", font=ctk.CTkFont(size=14, weight="bold"))
        self.status_label.pack(pady=(0, 10))
        self.prompt_input = ctk.CTkTextbox(main_frame, height=100, width=400, font=ctk.CTkFont(size=13))
        self.prompt_input.pack(pady=10)
        self.prompt_input.focus_set()
        self.submit_button = ctk.CTkButton(main_frame, text="Fill Form", command=self.submit_prompt)
        self.submit_button.pack(pady=10, fill='x')

    def center_window(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = int(screen_width/2 - width / 2)
        y = int(screen_height/2 - height / 2)
        return f'{width}x{height}+{x}+{y}'

    def submit_prompt(self):
        prompt_text = self.prompt_input.get("1.0", "end-1c").strip()
        self.prompt_input.configure(state="disabled")
        self.submit_button.configure(state="disabled")
        self.prompt_callback(prompt_text)

    def update_status(self, text):
        self.status_label.configure(text=text)
        self.update_idletasks()

    def close_window(self):
        self.destroy()

# --- Global Variables for State Management ---
ui_instance = None
user_prompt_from_ui = ""
ui_finished_event = threading.Event()
ai_engine = None # Will hold the pre-loaded AI engine

# --- Main Workflow (Simplified) ---
def run_fill_process():
    """The main application workflow, now with a much simpler pipeline."""
    if not process_lock.acquire(blocking=False):
        print("A fill process is already running.")
        return

    global ui_instance, user_prompt_from_ui
    
    def on_prompt_submit(prompt):
        global user_prompt_from_ui
        user_prompt_from_ui = prompt
        ui_finished_event.set()

    def start_ui_thread(callback_func):
        global ui_instance
        ui_instance = UIApp(callback_func)
        ui_instance.mainloop()

    ui_thread = threading.Thread(target=start_ui_thread, args=(on_prompt_submit,))
    ui_thread.daemon = True
    ui_thread.start()

    ui_finished_event.wait()

    try:
        # --- Stage 1: Get HTML from Browser ---
        ui_instance.update_status("Scanning page for form fields...")
        html_fields = trigger_and_wait_for_scan()
        if not html_fields:
            raise Exception("Failed to get HTML from extension.")
        print("\n--- 1. Raw HTML Snippets Received ---")
        print(json.dumps(html_fields, indent=2))
        print("-" * 35)

        # --- Stage 2: Generate Action Plan Directly (Single AI Call) ---
        ui_instance.update_status("Thinking... (Generating Action Plan)")
        
        # This is now the one and only call to the AI engine
        raw_action_plan = ai_engine.create_direct_action_plan(html_fields, user_prompt_from_ui)
        print("\n--- 2. Raw AI-Generated Action Plan ---")
        print(json.dumps(raw_action_plan, indent=2))
        print("-" * 37)

        # --- Stage 3: Cleanup AI Mistakes ---
        final_action_plan = cleanup_action_plan(raw_action_plan)
        print("\n--- 3. Final Cleaned Action Plan ---")
        print(json.dumps(final_action_plan, indent=2))
        print("-" * 35)

        # --- Stage 4: Execute Plan ---
        ui_instance.update_status("Filling form...")
        if final_action_plan:
            send_action_plan_to_host(final_action_plan)
        
        ui_instance.update_status("Done!")
        time.sleep(1.5)

    except Exception as e:
        print(f"\n--- An error occurred during the process ---\n{e}\n")
        if ui_instance:
            ui_instance.update_status(f"Error: {e}")
            time.sleep(3)
    finally:
        if ui_instance:
            ui_instance.close_window()
        ui_finished_event.clear()
        process_lock.release()

# --- AIEngine Class (Simplified) ---
class AIEngine:
    """A class to hold the simplified AI components (No VectorDB)."""
    def __init__(self):
        print("Initializing AI Engine... (This may take a moment)")
        # We now initialize the parser directly here, as it contains the new logic
        self.parser = form_filler_engine.Parser()
        print("✅ AI Engine ready.")

    def create_direct_action_plan(self, html_fields, user_prompt):
        """The new single method to generate the action plan."""
        return self.parser.create_action_plan(html_fields, user_prompt)

# --- Communication & Helper Functions (No major changes) ---
def trigger_and_wait_for_scan():
    data_received, data_event = None, threading.Event()
    def listener():
        nonlocal data_received
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); s.bind((HOST_IP, ORCHESTRATOR_PORT)); s.listen()
            conn, _ = s.accept()
            with conn:
                data_chunks = []
                while True:
                    chunk = conn.recv(4096)
                    if not chunk: break
                    data_chunks.append(chunk)
                data_received = json.loads(b''.join(data_chunks).decode('utf-8'))
                data_event.set()
    threading.Thread(target=listener, daemon=True).start()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST_IP, HOST_PORT)); s.sendall(json.dumps({"command": "scan"}).encode('utf-8'))
    return data_received if data_event.wait(timeout=30) else None

def send_action_plan_to_host(plan: list):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST_IP, HOST_PORT)); s.sendall(json.dumps({"command": "execute_plan", "payload": plan}).encode('utf-8'))

def cleanup_action_plan(plan: list):
    if not isinstance(plan, list): return []
    cleaned_plan, seen_selectors = [], set()
    for action in plan:
        if not (isinstance(action, dict) and all(k in action for k in ["selector", "action_type", "value"])): continue
        if action["selector"] in seen_selectors: continue
        if action["action_type"] == "FILL_TEXT" and isinstance(action["value"], bool): continue
        cleaned_plan.append(action)
        seen_selectors.add(action["selector"])
    return cleaned_plan

# --- Main Application Start ---
if __name__ == "__main__":
    # --- THIS IS THE SLOW, ONE-TIME STARTUP ---
    ai_engine = AIEngine() 
    
    print("\n--- SecureFill Orchestrator is Ready ---")
    print("Starting the UI...")
    
    # Directly call the main function to start the UI and run the process once.
    run_fill_process()

    print("\nApplication has finished its run.")
