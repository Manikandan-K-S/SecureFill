# trigger.py - The script you run to initiate a scan.

import socket

def send_scan_command():
    host, port = '127.0.0.1', 6000
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            s.sendall(b'scan')
        print("Successfully sent 'scan' command to the host application.")
    except ConnectionRefusedError:
        print("Connection failed. Is the host application running? (Was the browser started?)")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    input("Press Enter to send the scan command to the extension...")
    send_scan_command()