#!/bin/bash

# SSH Tunnel Startup Script
# Establishes tunnels for ports 8000-8004

# Configuration
JUMP_HOST="ubuntu@xxxxx"
TARGET_HOST="neurodx@1xxxxxx"
JUMP_PASSWORD="your_jump_password_here"
TARGET_PASSWORD="your_target_password_here"
PORTS=(8000 8001 8002 8003 8004)

echo "Starting SSH tunnels..."

# Function to create tunnel for a port
create_tunnel() {
    local port=$1
    
    # Using expect script
    expect << EOF &
    set timeout 30
    spawn ssh -N -L ${port}:localhost:${port} -J ${JUMP_HOST} ${TARGET_HOST} -o StrictHostKeyChecking=no -o ServerAliveInterval=60
    
    expect {
        "password:" {
            send "${JUMP_PASSWORD}\r"
            expect "password:" {
                send "${TARGET_PASSWORD}\r"
            }
        }
    }
    
    expect eof
EOF
    
    echo "✓ Started tunnel for port $port (PID: $!)"
    sleep 1
}

# Create tunnels for all ports
for port in "${PORTS[@]}"; do
    create_tunnel $port
done

echo "✓ All SSH tunnels started"
echo "Press Ctrl+C to stop all tunnels"

# Wait for user interrupt
wait