import tkinter as tk

# Create the main window
root = tk.Tk()
root.title("Hello World App")
root.geometry("300x200")

# Create a label widget
hello_label = tk.Label(root, text="Hello, World!", font=("Arial", 24))
hello_label.pack(pady=50)

# Start the Tkinter event loop
root.mainloop()
