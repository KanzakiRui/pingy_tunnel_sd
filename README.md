# File: extensions/sd-webui-tunnel/scripts/tunnel_extension.py
# (This is where the main extension code goes - copy the previous artifact content here)

# File: extensions/sd-webui-tunnel/install.py
import os
import subprocess
import sys

def install_requirements():
    """Install any required packages"""
    print("Installing tunnel extension requirements...")
    # Add any pip install commands here if needed
    # subprocess.check_call([sys.executable, "-m", "pip", "install", "package_name"])
    print("Tunnel extension requirements installed successfully!")

if __name__ == "__main__":
    install_requirements()

# File: extensions/sd-webui-tunnel/requirements.txt
# Add any Python package requirements here
# (Currently no additional packages needed beyond what A1111 already has)

# File: extensions/sd-webui-tunnel/README.md
# Pinggy Tunnel Extension for Automatic1111 WebUI

This extension adds tunnel support to Automatic1111 WebUI using pinggy.io, allowing external access to your WebUI without port forwarding or firewall configuration.

## Features

- Easy external access via pinggy.io tunnels
- Command line arguments similar to ngrok
- Automatic URL detection and display
- Proper cleanup on exit
- Logging support

## Installation

1. Clone or download this extension to your `extensions` folder:
   ```bash
   cd extensions
   git clone <repository-url> sd-webui-tunnel
   ```

2. Restart your WebUI

## Usage

Add the `--tunnel` argument when starting your WebUI:

```bash
python launch.py --tunnel
```

Or specify a custom port:

```bash
python launch.py --tunnel --tunnel-port 8080
```

## Command Line Arguments

- `--tunnel`: Enable pinggy tunnel for external access
- `--tunnel-port <port>`: Specify port for tunnel (defaults to WebUI port)

## How it Works

The extension creates an SSH tunnel to pinggy.io which provides a temporary public URL that forwards to your local WebUI. The URL will be displayed in the console when the tunnel is established.

## Notes

- The tunnel URL is temporary and will change each time you restart
- Requires internet connection to establish tunnel
- SSH connection uses port 80
- Tunnel logs are saved to `.cache/pigy.log`

## Troubleshooting

If you encounter issues:

1. Check the logs in `.cache/pigy.log`
2. Ensure you have internet connectivity
3. Make sure SSH is available on your system
4. Check that port 80 is not blocked by your firewall

## Security Notice

This extension exposes your WebUI to the internet. Only use this for legitimate purposes and be aware that your WebUI will be publicly accessible via the generated URL.
