import os
import sys
import time
import subprocess
import threading
from pathlib import Path
import logging
import gradio as gr
from modules import script_callbacks, shared

# Extension info
extension_name = "Pinggy Tunnel"

# Ensure .cache directory exists
cache_dir = Path('.cache')
cache_dir.mkdir(parents=True, exist_ok=True)

# Set up logging
log_file = cache_dir / 'tunnel_extension.log'
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

class PinggyTunnel:
    def __init__(self):
        self.tunnel_process = None
        self.url_monitor_thread = None
        self.tunnel_url = None
        self.is_running = False
        self.output_file = cache_dir / 'pigy.txt'
        self.enabled = False
        
    def start_tunnel(self, local_port):
        """Start the pinggy tunnel"""
        if self.is_running:
            logging.warning("Tunnel is already running")
            return
            
        logging.info(f"Starting SSH tunnel on port 80 and forwarding to localhost:{local_port}...")
        print(f"\n🚀 Starting Pinggy Tunnel on port {local_port}...")
        print("⏳ Please wait while we establish the connection...")
        
        try:
            # Clean up any existing output file
            if self.output_file.exists():
                self.output_file.unlink()
                
            # Start the SSH tunnel in a separate thread
            tunnel_command = f'ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 80 -R0:localhost:{local_port} a.pinggy.io > {self.output_file} 2>&1'
            
            def run_tunnel():
                try:
                    self.tunnel_process = subprocess.Popen(tunnel_command, shell=True)
                    self.tunnel_process.wait()
                except Exception as e:
                    logging.error(f"Tunnel process error: {e}")
            
            tunnel_thread = threading.Thread(target=run_tunnel, daemon=True)
            tunnel_thread.start()
            
            # Start URL monitoring in a separate thread
            self.url_monitor_thread = threading.Thread(target=self._monitor_url, daemon=True)
            self.url_monitor_thread.start()
            
            self.is_running = True
            logging.info("Tunnel started successfully")
            
        except Exception as e:
            logging.error(f"Error starting tunnel: {e}")
            print(f"❌ Error starting tunnel: {e}")
    
    def _monitor_url(self, timeout=60):
        """Monitor for the tunnel URL"""
        start_time = time.time()
        
        while time.time() - start_time < timeout and self.is_running:
            time.sleep(3)
            
            try:
                if self.output_file.exists():
                    with open(self.output_file, 'r') as file:
                        content = file.read()
                        
                        # Look for HTTP URL
                        for line in content.split('\n'):
                            if 'http://' in line and '.pinggy.link' in line:
                                # Extract URL more carefully
                                start_idx = line.find('http://')
                                if start_idx != -1:
                                    end_idx = line.find(' ', start_idx)
                                    if end_idx == -1:
                                        end_idx = len(line)
                                    
                                    url = line[start_idx:end_idx].strip()
                                    if url.endswith('.pinggy.link') or '.pinggy.link' in url:
                                        self.tunnel_url = url
                                        logging.info(f"Found URL: {url}")
                                        print(f'\n🌐 Pinggy Tunnel URL: {url}')
                                        print(f'🔗 Your WebUI is now accessible at: {url}')
                                        print(f'📝 Note: This URL is temporary and will change on restart\n')
                                        return
                        
                        # Also check for any errors
                        if 'connection' in content.lower() and 'failed' in content.lower():
                            print("❌ Connection failed. Please check your internet connection.")
                            logging.error("SSH connection failed")
                            break
                            
            except Exception as e:
                logging.error(f"Error reading tunnel output: {e}")
        
        if self.is_running:
            print("\n⏰ Timeout reached, tunnel URL not found.")
            print("This might be due to network issues or pinggy.io being unavailable.")
            print("Check the log file for more details: .cache/tunnel_extension.log\n")
    
    def stop_tunnel(self):
        """Stop the tunnel"""
        if not self.is_running:
            return
            
        self.is_running = False
        
        if self.tunnel_process:
            try:
                self.tunnel_process.terminate()
                time.sleep(2)
                if self.tunnel_process.poll() is None:
                    self.tunnel_process.kill()
            except Exception as e:
                logging.error(f"Error stopping tunnel process: {e}")
        
        # Clean up output file
        try:
            if self.output_file.exists():
                self.output_file.unlink()
        except Exception as e:
            logging.error(f"Error cleaning up output file: {e}")
            
        logging.info("Tunnel stopped")
        print("🔌 Tunnel stopped")

# Global tunnel instance
tunnel_instance = PinggyTunnel()

def create_tunnel_interface():
    """Create Gradio interface for tunnel control"""
    with gr.Group():
        gr.Markdown("## 🚇 Pinggy Tunnel Control")
        gr.Markdown("Create a public tunnel to access your WebUI from anywhere!")
        
        with gr.Row():
            tunnel_port = gr.Number(
                label="Port", 
                value=7860, 
                precision=0,
                info="Port to tunnel (usually 7860 for WebUI)"
            )
            
        with gr.Row():
            start_btn = gr.Button("🚀 Start Tunnel", variant="primary")
            stop_btn = gr.Button("🛑 Stop Tunnel", variant="secondary")
            
        tunnel_status = gr.Textbox(
            label="Tunnel Status", 
            value="Not running",
            interactive=False
        )
        
        tunnel_url_display = gr.Textbox(
            label="Public URL", 
            value="No tunnel active",
            interactive=False
        )
    
    def start_tunnel_handler(port):
        try:
            port = int(port)
            if port < 1 or port > 65535:
                return "❌ Invalid port number", "Error"
            
            if tunnel_instance.is_running:
                return "⚠️ Tunnel already running", tunnel_instance.tunnel_url or "Starting..."
            
            tunnel_instance.start_tunnel(port)
            return "🟡 Starting tunnel...", "Please wait..."
            
        except Exception as e:
            return f"❌ Error: {str(e)}", "Error"
    
    def stop_tunnel_handler():
        tunnel_instance.stop_tunnel()
        return "🔴 Tunnel stopped", "No tunnel active"
    
    def get_status():
        if tunnel_instance.is_running:
            if tunnel_instance.tunnel_url:
                return "🟢 Tunnel active", tunnel_instance.tunnel_url
            else:
                return "🟡 Connecting...", "Please wait..."
        else:
            return "🔴 Not running", "No tunnel active"
    
    start_btn.click(
        start_tunnel_handler,
        inputs=[tunnel_port],
        outputs=[tunnel_status, tunnel_url_display]
    )
    
    stop_btn.click(
        stop_tunnel_handler,
        outputs=[tunnel_status, tunnel_url_display]
    )
    
    # Auto-refresh status every 5 seconds
    def auto_refresh():
        while True:
            time.sleep(5)
            if hasattr(tunnel_instance, 'tunnel_url') and tunnel_instance.tunnel_url:
                break
    
    return [(tunnel_status, tunnel_url_display)]

def on_ui_tabs():
    """Add tunnel tab to the WebUI"""
    with gr.Blocks() as tunnel_tab:
        create_tunnel_interface()
    
    return [(tunnel_tab, "Tunnel", "tunnel")]

def on_app_started(demo, app):
    """Called when the app starts - check for environment variables"""
    
    # Check for environment variable to auto-start tunnel
    auto_tunnel = os.environ.get('WEBUI_TUNNEL', '').lower() in ['1', 'true', 'yes']
    tunnel_port = int(os.environ.get('WEBUI_TUNNEL_PORT', '7860'))
    
    if auto_tunnel:
        print(f"\n🔧 Auto-starting tunnel (WEBUI_TUNNEL=true)")
        tunnel_instance.start_tunnel(tunnel_port)

# Register callbacks
script_callbacks.on_ui_tabs(on_ui_tabs)
script_callbacks.on_app_started(on_app_started)

# Handle cleanup on exit
import atexit
atexit.register(lambda: tunnel_instance.stop_tunnel())

print(f"✅ {extension_name} extension loaded")
print("💡 Use the 'Tunnel' tab in WebUI to start/stop tunnels")
print("💡 Or set environment variable: WEBUI_TUNNEL=true")
