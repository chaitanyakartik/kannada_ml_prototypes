"""
SSH Tunnel Manager for AI Tools Suite
Establishes SSH tunnels to backend services through jump host
"""

import subprocess
import time
import os
import atexit
import signal
from pathlib import Path
from dotenv import load_dotenv

# Load variables from .env file in the same directory as this script
# env_path = Path(__file__).parent / '.env'
load_dotenv()

# SSH Configuration
JUMP_HOST = os.getenv("JUMPHOST")
TARGET_HOST = os.getenv("TARGETHOST")

# Removed 8000 since it was flagged as in-use; sticking to your requested list
PORTS = [8001, 8002, 8003, 8004]

# Passwords
JUMP_PASSWORD = os.getenv("JUMP_PASSWORD")
TARGET_PASSWORD = os.getenv("TARGET_PASSWORD")

if not JUMP_HOST or not TARGET_HOST:
    raise ValueError("Missing JUMPHOST or TARGETHOST in .env file")

if __name__ == "__main__" or os.getenv("DEBUG_TUNNELS"):
    print(f"[Tunnel Manager] Config loaded from: {env_path}")
    print(f"[Tunnel Manager] JUMPHOST: {JUMP_HOST}")
    print(f"[Tunnel Manager] TARGETHOST: {TARGET_HOST}")

class TunnelManager:
    def __init__(self):
        self.processes = []
        atexit.register(self.cleanup)
    
    def create_tunnel_with_expect(self, port):
        """Create SSH tunnel using expect for password handling"""
        # Removed "Connection established" as -N doesn't return that.
        # Added 'exp_continue' to handle multiple password prompts sequentially.
        expect_script = f"""
set timeout 20
spawn ssh -N -L {port}:localhost:{port} -J {JUMP_HOST} {TARGET_HOST} -o StrictHostKeyChecking=no -o ServerAliveInterval=60

expect {{
    "password:" {{
        send "{JUMP_PASSWORD}\\r"
        expect {{
            "password:" {{
                send "{TARGET_PASSWORD}\\r"
                exp_continue
            }}
        }}
    }}
    timeout {{
        exit 1
    }}
    eof {{
        exit 0
    }}
}}
# Keep the process alive
interact
"""
        
        try:
            process = subprocess.Popen(
                ['expect', '-c', expect_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                preexec_fn=os.setsid # Create a process group for easier cleanup
            )
            
            self.processes.append({'port': port, 'process': process})
            return True
        except Exception as e:
            print(f"Error creating tunnel for port {port}: {e}")
            return False
    
    def create_tunnel_with_keys(self, port):
        cmd = [
            'ssh', '-N',
            '-L', f'{port}:localhost:{port}',
            '-J', JUMP_HOST,
            TARGET_HOST,
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'ServerAliveInterval=60'
        ]
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes.append({'port': port, 'process': process})
            return True
        except Exception as e:
            print(f"Error creating tunnel for port {port}: {e}")
            return False
    
    def start_all_tunnels(self):
        use_passwords = bool(JUMP_PASSWORD or TARGET_PASSWORD)
        
        # Kill any existing tunnels on these ports first to avoid "Address already in use"
        for port in PORTS:
            subprocess.run(f"lsof -ti:{port} | xargs kill -9", shell=True, stderr=subprocess.DEVNULL)
            
            if use_passwords:
                success = self.create_tunnel_with_expect(port)
            else:
                success = self.create_tunnel_with_keys(port)
            
            if success:
                time.sleep(0.5) # Staggering prevents auth collisions
        
        time.sleep(2)
        return self.check_active_tunnels()
    
    def check_active_tunnels(self):
        active = []
        for tunnel in self.processes:
            if tunnel['process'].poll() is None:
                active.append(tunnel['port'])
        return active
    
    def cleanup(self):
        for tunnel in self.processes:
            try:
                # Kill the whole process group (expect + ssh)
                os.killpg(os.getpgid(tunnel['process'].pid), signal.SIGTERM)
            except:
                pass

_manager = None

def initialize_tunnels():
    global _manager
    if _manager is None:
        _manager = TunnelManager()
        active_ports = _manager.start_all_tunnels()
        
        if len(active_ports) == len(PORTS):
            print(f"✓ All {len(active_ports)} SSH tunnels established")
        else:
            print(f"⚠ Warning: Only {len(active_ports)}/{len(PORTS)} tunnels active")
            print(f"Active ports: {active_ports}")
    return _manager

def get_tunnel_status():
    return _manager.check_active_tunnels() if _manager else []