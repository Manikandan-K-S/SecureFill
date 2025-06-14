import os
import subprocess
import sys
import threading

try:
    import keyboard
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'keyboard'])
    import keyboard

TRIGGER_SCRIPT = os.path.join(os.path.dirname(__file__), 'trigger.py')


def run_trigger():
    print("Hotkey pressed! Running trigger.py...")
    subprocess.Popen([sys.executable, TRIGGER_SCRIPT], shell=False)


def listen_hotkey():
    print("Registering global hotkey: Ctrl+Shift+F")
    keyboard.add_hotkey('ctrl+shift+f', run_trigger)
    print("Hotkey registered. Waiting for hotkey press...")
    keyboard.wait()  # Block forever


def main():
    t = threading.Thread(target=listen_hotkey, daemon=True)
    t.start()
    t.join()

if __name__ == '__main__':
    main()
