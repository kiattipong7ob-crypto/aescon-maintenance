import os
import sys
import threading
import time
import urllib.request
from http.server import HTTPServer

# Ensure project directory is in sys.path
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

from server import MaintenanceHandler, run

def start_server_thread(port=8000):
    server_address = ('127.0.0.1', port)
    try:
        httpd = HTTPServer(server_address, MaintenanceHandler)
        httpd.serve_forever()
    except Exception as e:
        print(f"Server thread ended or port in use: {e}")

def wait_for_server(url="http://127.0.0.1:8000/api/stats", timeout=10):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url) as response:
                if response.status == 200:
                    return True
        except Exception:
            time.sleep(0.2)
    return False

def main():
    port = 8000

    # Start server in background thread
    t = threading.Thread(target=start_server_thread, args=(port,), daemon=True)
    t.start()

    # Wait for server to start
    wait_for_server(f"http://127.0.0.1:{port}/api/stats")

    # Launch Native Desktop Window
    try:
        import webview
        window = webview.create_window(
            title='AESCON Maintenance - ระบบตรวจสอบและบำรุงรักษาเครื่องมือ (F-MT-68)',
            url=f'http://127.0.0.1:{port}/',
            width=1380,
            height=900,
            min_size=(1024, 700),
            resizable=True,
            text_select=True,
            confirm_close=False
        )
        webview.start(gui='edgechromium', debug=False)
    except Exception as e:
        print(f"Webview error, falling back to browser / app mode: {e}")
        # Fallback to Edge App Mode or standard browser
        edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        if os.path.exists(edge_path):
            import subprocess
            subprocess.run([edge_path, f"--app=http://127.0.0.1:{port}", "--window-size=1380,900"])
        else:
            import webbrowser
            webbrowser.open(f"http://127.0.0.1:{port}")

if __name__ == '__main__':
    main()
