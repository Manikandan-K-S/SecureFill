import socket
import threading
import json
import time
import sys
from pynput import keyboard # For global hotkeys
import customtkinter as ctk # For the UI

# Import the form-filling engine we built
from modelEngine import parser as form_filler_engine

# --- Configuration ---
HOST_IP = '127.0.0.1'
ORCHESTRATOR_PORT = 6001 
HOST_PORT = 6000
# Define your hotkey. This is for Ctrl + Alt + F
HOTKEY = {keyboard.Key.ctrl, keyboard.Key.shift, keyboard.KeyCode.from_char('f')}
current_keys = set()


# --- UI Application Class ---
# We wrap the UI in a class to easily manage its state and components.
class UIApp(ctk.CTk):
    def __init__(self, prompt_callback):
        super().__init__()
        self.prompt_callback = prompt_callback # This function is called when the user clicks "Fill"

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
        """Calculates the x, y coordinates to center the window."""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = int(screen_width/2 - width / 2)
        y = int(screen_height/2 - height / 2)
        return f'{width}x{height}+{x}+{y}'

    def submit_prompt(self):
        """Gets text, disables UI, and calls the main logic."""
        prompt_text = self.prompt_input.get("1.0", "end-1c").strip()
        self.prompt_input.configure(state="disabled")
        self.submit_button.configure(state="disabled")
        self.prompt_callback(prompt_text) # Send the prompt back to the main thread

    def update_status(self, text):
        """Allows the main thread to update the UI's status label."""
        self.status_label.configure(text=text)

    def close_window(self):
        """Closes the UI window."""
        self.destroy()

# --- Global Variables for State Management ---
ui_instance = None
user_prompt_from_ui = ""
ui_finished_event = threading.Event()

def start_ui_thread(callback_func):
    global ui_instance
    ui_instance = UIApp(callback_func)
    ui_instance.mainloop()

# --- Main Workflow ---
def run_fill_process():
    """This is the main function triggered by the hotkey."""
    global ui_instance, user_prompt_from_ui
    
    # Define the callback function for the UI
    def on_prompt_submit(prompt):
        global user_prompt_from_ui
        user_prompt_from_ui = prompt
        ui_finished_event.set() # Signal that the user has submitted the prompt

    # Create and run the UI in a separate thread
    ui_thread = threading.Thread(target=start_ui_thread, args=(on_prompt_submit,))
    ui_thread.daemon = True
    ui_thread.start()

    # Wait for the user to submit the prompt in the UI
    ui_finished_event.wait()

    try:
        # --- The AI Pipeline Begins ---
        # 1. Update UI and trigger scan
        ui_instance.update_status("Scanning page...")
        html_fields = trigger_and_wait_for_scan()
        if not html_fields:
            raise Exception("Failed to get HTML from extension.")

        # 2. Initialize engine
        ui_instance.update_status("Waking up AI...")
        config = form_filler_engine.load_config()
        llm = form_filler_engine.initialize_llm(config)
        vectorstore = form_filler_engine.initialize_vectorstore()
        if not all([config, llm, vectorstore]):
            raise Exception("Failed to initialize AI engine.")

        analyze_chain = form_filler_engine.analysis_prompt | llm | form_filler_engine.StrOutputParser()
        action_plan_chain = form_filler_engine.action_plan_prompt | llm | form_filler_engine.StrOutputParser()

        # 3. Run analysis
        ui_instance.update_status("Analyzing form fields...")
        analysis_plan = form_filler_engine.analyze_form_and_create_search_plan(analyze_chain, html_fields, user_prompt_from_ui)
        if not analysis_plan:
            raise Exception("AI failed to create an analysis plan.")

        # 4. Run search
        ui_instance.update_status("Searching for your data...")
        search_results = form_filler_engine.search_vector_db(vectorstore, analysis_plan, top_k=2)

        # 5. Generate final plan
        ui_instance.update_status("Creating final action plan...")
        raw_action_plan = form_filler_engine.generate_action_plan(action_plan_chain, search_results, user_prompt_from_ui)
        final_action_plan = cleanup_action_plan(raw_action_plan)

        # 6. Execute plan
        ui_instance.update_status("Filling form...")
        if final_action_plan:
            send_action_plan_to_host(final_action_plan)
        
        ui_instance.update_status("Done!")
        time.sleep(1.5) # Give user time to see "Done!"

    except Exception as e:
        print(f"An error occurred: {e}")
        if ui_instance:
            ui_instance.update_status(f"Error: {e}")
            time.sleep(3)
    finally:
        # Clean up
        if ui_instance:
            ui_instance.close_window()
        ui_finished_event.clear()


# --- Communication & Helper Functions (modified for the new flow) ---
def trigger_and_wait_for_scan():
    """Triggers the scan and waits for the data to be returned via a socket."""
    data_received = None
    data_event = threading.Event()

    def listener():
        nonlocal data_received
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST_IP, ORCHESTRATOR_PORT))
            s.listen()
            conn, _ = s.accept()
            with conn:
                data_chunks = []
                while True:
                    chunk = conn.recv(4096)
                    if not chunk: break
                    data_chunks.append(chunk)
                raw_data = b''.join(data_chunks).decode('utf-8')
                data_received = json.loads(raw_data)
                data_event.set()

    listener_thread = threading.Thread(target=listener)
    listener_thread.daemon = True
    listener_thread.start()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST_IP, HOST_PORT))
        s.sendall(json.dumps({"command": "scan"}).encode('utf-8'))
    
    success = data_event.wait(timeout=30)
    return data_received if success else None

def send_action_plan_to_host(plan: list):
    """Sends the final plan to the host for execution."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST_IP, HOST_PORT))
        command = {"command": "execute_plan", "payload": plan}
        s.sendall(json.dumps(command).encode('utf-8'))

def cleanup_action_plan(plan: list):
    """Removes duplicates and bad values from the AI's plan."""
    if not isinstance(plan, list): return []
    cleaned_plan, seen_selectors = [], set()
    for action in plan:
        if not (isinstance(action, dict) and all(k in action for k in ["selector", "action_type", "value"])): continue
        if action["selector"] in seen_selectors: continue
        if action["action_type"] == "FILL_TEXT" and isinstance(action["value"], bool): continue
        cleaned_plan.append(action)
        seen_selectors.add(action["selector"])
    return cleaned_plan

# --- Hotkey Listener Setup ---
def on_press(key):
    """Checks if the hotkey combination is pressed."""
    if key in HOTKEY:
        current_keys.add(key)
        if all(k in current_keys for k in HOTKEY):
            print("Hotkey activated! Running fill process...")
            # Run the main process in a separate thread to not block the listener
            threading.Thread(target=run_fill_process).start()

def on_release(key):
    """Removes keys from the set on release."""
    try:
        current_keys.remove(key)
    except KeyError:
        pass

# --- Main Application Start ---
# if __name__ == "__main__":
#     print("--- SecureFill Orchestrator Engine ---")
#     print(f"Press {' + '.join([str(k).split('.')[-1] for k in HOTKEY])} to activate.")
#     print("This window must remain open. You can minimize it.")
    
#     # Start listening for the hotkey
#     with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
#         listener.join()

if __name__ == "__main__":
    print("--- SecureFill Orchestrator Engine ---")
    print("Starting the application directly (no hotkey).")
    
    # Directly call the main function to start the UI and the fill process.
    # This runs the whole process once.
    run_fill_process()

    print("\nApplication has finished its run.")
