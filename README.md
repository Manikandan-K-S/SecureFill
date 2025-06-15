# SecureFill: Your Private AI Form-Filling Assistant

## 🚀 Application Description

**SecureFill** is a privacy-first, edge AI assistant that revolutionizes the process of filling online forms. It runs entirely on the user's local machine, ensuring that sensitive personal data such as names, emails, addresses, and other details never leave the device.

Triggered by a simple keyboard shortcut, SecureFill intelligently analyzes the structure and context of web forms on the user's active browser tab. By leveraging a local AI model and a secure vector database, it retrieves the correct personal information and populates the form fields automatically. The user can guide the process with natural language prompts, providing a seamless, secure, and highly efficient form-filling experience.

## 👥 Team Members

| Name                | Email                     |
| ------------------- | ------------------------- |
| Manikandan K S      | mani.ks1324579@gmail.com  |
| Rishi Sundaresan    | rishisundaresan51@gmail.com |
| Sharun A            | sharunaravind6888@gmail.com |
| Vijay Sharvesh      | vijaysharvesh16@gmail.com   |
| Ramya R             | ramyaraja1120@gmail.com  |

## 🛠️ Setup Instructions (From Scratch)

Follow these steps to set up and run SecureFill on your local machine.

### Prerequisites

* **Python 3.10+** installed on your system.
* **Chromium based** browser.
* **Git** for cloning the repository.

### Step 1: Set Up the Python Backend

This will prepare the local environment that runs the AI and communicates with the browser.

1.  **Clone the Repository:**
    Open a terminal or command prompt and clone the project files.
    ```bash
    git clone https://github.com/Manikandan-K-S/SecureFill
    cd SecureFill
    ```

2.  **Create and Activate a Virtual Environment:**
    This isolates the project's dependencies from your system's Python installation.
    ```bash
    # Create the virtual environment
    python -m venv venv

    # Activate it
    # On Windows:
    .\venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install Dependencies:**
    Install all required Python libraries from the `requirements.txt` file.
    ```bash
    pip install -r requirements.txt
    ```

### Step 2: Register the Native Messaging Host

This is a crucial one-time setup step that allows Google Chrome to securely launch and communicate with your Python application.

**On Windows:**
1.  Navigate to the `Extensions/python_host/` directory in your file explorer.
2.  Find the file named **`register_host.reg`**.
3.  **Double-click** this file. You will see a security prompt from the Registry Editor.
4.  Click **"Yes"** and then **"OK"** to add the necessary keys to the Windows Registry. This tells Chrome where to find your `host.py` application.


### Step 3: Load the Chrome Extension

1.  Open Google Chrome and navigate to the extensions page: `chrome://extensions`.
2.  In the top-right corner, toggle on **"Developer mode"**.
3.  Click the **"Load unpacked"** button that appears on the top-left.
4.  In the file selection dialog, navigate to and select the `Extensions/browser_extension` folder from the project directory.
5.  The "SecureFill" extension should now appear in your list of extensions. Click the puzzle piece icon in your Chrome toolbar and "pin" it for easy access.

The setup is now complete!

### Step 4: Connect the Extension to the Host

This crucial step creates the secure "handshake" that allows your Python application to trust and communicate with your Chrome extension.

1.  **Find Your Extension ID:** On the `chrome://extensions` page, look at the card for your newly loaded "SecureFill" extension. You will see an **ID** field with a long string of letters (e.g., `fmkadmapgofadopljbjfapgipbfaaaaa`). Click the "copy" icon next to it.

2.  **Update the Host Manifest File:**
    * Navigate to the `Extensions/python_host/` directory in your code editor.
    * Open the file named **`com.my_ai_app.native_host.json`**.

3.  **Paste the ID:** Inside that file, you will see a section called `"allowed_origins"`. You must paste your extension's ID into this array.

    ```json
    {
      "name": "com.my_ai_app.native_host",
      "description": "SecureFill AI assistant.",
      "path": "ABSOLUTE_PATH_TO_YOUR_host.py",
      "type": "stdio",
      "allowed_origins": [
        "chrome-extension://YOUR_COPIED_ID_GOES_HERE/"
      ]
    }
    ```
    > **Important:** Replace `YOUR_COPIED_ID_GOES_HERE` with the actual ID you copied. Make sure the `chrome-extension://` prefix and the trailing `/` are kept.

4.  **Reload the Extension:** Go back to the `chrome://extensions` page and click the **reload icon** on your extension's card. This ensures it's aware of the new permissions and can establish the connection.

## ▶️ How to Run and Use SecureFill

The application consists of two main Python processes that need to be running in the background.

## ▶️ How to Run and Use SecureFill

The application is designed to be seamless. Once set up, you only need to run a single script in the background to enable the hotkey functionality.

### Step 1: Start the Hotkey Listener

You only need to start one service manually. This script will run silently in the background and wait for you to press the activation hotkey.

1.  Open a terminal or command prompt.
2.  Make sure your Python virtual environment is activated:
    * On Windows: `.\venv\Scripts\activate`
    * On macOS/Linux: `source venv/bin/activate`
3.  Navigate to the project's root directory.
4.  Run the hotkey listener script:
    ```bash
    python /main.py
    ```

You should see a message confirming the listener is active. You can now minimize this terminal window.

> **Note:** You do **not** need to run `host.py` manually. The Google Chrome browser will automatically launch `host.py` in the background as needed, thanks to the Native Messaging setup. This is a core feature of the secure architecture.


### Step 2: Using the Application

1.  Navigate to any webpage in Google Chrome that contains a form you want to fill.
2.  Press the global hotkey **`Ctrl+Alt+F`**.
3.  The **SecureFill Assistant** UI window will appear on top of your browser.
4.  Type a prompt with any specific instructions (e.g., "Use my work email" or just "Fill this form").
5.  Click the **"Fill Form"** button.
6.  The UI will close, and the extension will receive the AI-generated plan and automatically populate the fields on the webpage.
7.  If a field is filled incorrectly or you want to change the data, press the hotkey again and provide a more specific prompt (e.g., "Leave the phone number blank").
