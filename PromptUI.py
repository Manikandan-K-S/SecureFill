import customtkinter as ctk
import socket
import json
import sys

# Before running, make sure you have installed the library:
# pip install customtkinter

def send_prompt_to_host():
    """Sends the user's prompt back to the main host.py script."""
    user_prompt = prompt_input.get("1.0", "end-1c").strip()
    
    # This is the data structure we send back
    message_to_host = {
        "user_prompt": user_prompt
    }
    
    # We use a socket to send the data back. This is simple and effective
    # for one-time communication between two local Python scripts.
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 6001)) # The private port host.py listens on
            s.sendall(json.dumps(message_to_host).encode('utf-8'))
        
        # Close the UI window after sending
        root.destroy()
    except ConnectionRefusedError:
        print("UI Error: Could not connect to host on port 6001. Is it running?")
        root.destroy()

# --- UI Setup ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("SecureFill Assistant")
root.attributes('-topmost', True) # Keep window on top

main_frame = ctk.CTkFrame(root)
main_frame.pack(pady=20, padx=20, fill="both", expand=True)

prompt_label = ctk.CTkLabel(main_frame, text="What would you like to do?", font=ctk.CTkFont(size=14, weight="bold"))
prompt_label.pack(pady=(0, 10))

prompt_input = ctk.CTkTextbox(main_frame, height=80, width=350, font=ctk.CTkFont(size=12))
prompt_input.pack(pady=10)
prompt_input.focus_set() # Focus the text box on launch

submit_button = ctk.CTkButton(main_frame, text="Fill Form", command=send_prompt_to_host)
submit_button.pack(pady=10, fill='x')

# Center the window
window_width = 400
window_height = 250
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
center_x = int(screen_width/2 - window_width / 2)
center_y = int(screen_height/2 - window_height / 2)
root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

root.mainloop()
