import os
import sys
import time
import subprocess
import threading
from pathlib import Path
import logging
import modules.shared as shared
from modules import script_callbacks

# Extension info
extension_name = "Pinggy Tunnel"
extension_description = "Adds tunnel support using pinggy.io for external access"

# Ensure .cache directory exists
cache_dir = Path('.cache')
cache_dir.mkdir(parents=True, exist_ok=True)

# Set up logging
logging.basicConfig(
    filename=cache_dir / 'pigy.log', 
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a'
)

class PinggyTunnel:
    def __init__(self):
        self.tunnel_process = None
        self.url_monitor_thread = None
        self.tunnel_url = None
        self.is_running = False
        self.output_file = cache_dir / 'pigy.txt'
        
    def start_tunnel(self, local_port):
        """Start the pinggy tunnel"""
        if self.is_running:
            logging.warning("Tunnel is already running")
            return
            
        logging.info(f"Starting SSH tunnel on port 80 and forwarding to localhost:{local_port}...")
        
        try:
            # Clean up any existing output file
            if self.output_file.exists():
                self.output_file.unlink()
                
            # Start the SSH tunnel in a separate thread
            tunnel_command = f'ssh -o StrictHostKeyChecking=no -p 80 -R0:localhost:{local_port} a.pinggy.io > {self.output_file}'
            self.tunnel_process = subprocess.Popen(tunnel_command, shell=True)
            
            # Start URL monitoring in a separate thread
            self.url_monitor_thread = threading.Thread(target=self._monitor_url, daemon=True)
            self.url_monitor_thread.start()
            
            self.is_running = True
            logging.info("Tunnel started successfully")
            
        except Exception as e:
            logging.error(f"Error starting tunnel: {e}")
            print(f"Error starting tunnel: {e}")
    
    def _monitor_url(self, timeout=30):
        """Monitor for the tunnel URL"""
        start_time = time.time()
        
        while time.time() - start_time < timeout and self.is_running:
            time.sleep(2)
            logging.info("Checking for URL...")
            
            try:
                if self.output_file.exists():
                    with open(self.output_file, 'r') as file:
                        content = file.read()
                        for line in content.split('\n'):
                            if 'http:' in line and '.pinggy.link' in line:
                                url = line[line.find('http:'):line.find('.pinggy.link') + len('.pinggy.link')]
                                self.tunnel_url = url
                                logging.info(f"Found URL: {url}")
                                print(f'\n🌐 Pinggy Tunnel URL: {url}\n')
                                print(f'🔗 Your WebUI is now accessible at: {url}')
                                print(f'📝 Note: This URL is temporary and will change on restart\n')
                                return
                                
            except FileNotFoundError:
                logging.warning(f"File not found: {self.output_file}")
            except Exception as e:
                logging.error(f"Error reading file: {e}")
        
        if self.is_running:
            logging.error("Timeout reached, URL not found.")
            print("\n❌ Timeout reached, tunnel URL not found.")
            print("Please check your internet connection and try again.\n")
    
    def stop_tunnel(self):
        """Stop the tunnel"""
        if not self.is_running:
            return
            
        self.is_running = False
        
        if self.tunnel_process:
            try:
                self.tunnel_process.terminate()
                self.tunnel_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
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

def add_tunnel_args():
    """Add tunnel-related command line arguments"""
    import argparse
    
    # Get the existing parser
    parser = shared.parser if hasattr(shared, 'parser') else argparse.ArgumentParser()
    
    # Add tunnel arguments
    parser.add_argument(
        '--tunnel', 
        action='store_true', 
        help='Enable pinggy tunnel for external access'
    )
    
    parser.add_argument(
        '--tunnel-port',
        type=int,
        default=None,
        help='Specify port for tunnel (defaults to WebUI port)'
    )

def on_app_started(demo, app):
    """Called when the WebUI app starts"""
    global tunnel_instance
    
    # Check if tunnel is enabled
    if hasattr(shared.cmd_opts, 'tunnel') and shared.cmd_opts.tunnel:
        # Determine the port to use
        tunnel_port = getattr(shared.cmd_opts, 'tunnel_port', None)
        if tunnel_port is None:
            tunnel_port = shared.cmd_opts.port if hasattr(shared.cmd_opts, 'port') else 7860
        
        print(f"\n🚀 Starting Pinggy Tunnel on port {tunnel_port}...")
        print("⏳ Please wait while we establish the connection...")
        
        tunnel_instance.start_tunnel(tunnel_port)

def on_script_unloaded():
    """Called when the script is unloaded"""
    global tunnel_instance
    tunnel_instance.stop_tunnel()

# Register callbacks
script_callbacks.on_app_started(on_app_started)
script_callbacks.on_script_unloaded(on_script_unloaded)

# Add arguments when the module is imported
try:
    add_tunnel_args()
except Exception as e:
    logging.error(f"Error adding tunnel arguments: {e}")

# Handle cleanup on exit
import atexit
atexit.register(lambda: tunnel_instance.stop_tunnel())

print(f"✅ {extension_name} extension loaded")
print("💡 Use --tunnel to enable external access via pinggy.io")
print("💡 Use --tunnel-port <port> to specify a custom port")
