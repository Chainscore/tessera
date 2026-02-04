
import os
import signal
import subprocess
import time

def kill_port(port):
    try:
        # lsof -i :port -t
        # This returns PIDs
        result = subprocess.run(["lsof", "-i", f":{port}", "-t"], capture_output=True, text=True)
        pids = result.stdout.strip().split('\n')
        for pid in pids:
            if pid:
                print(f"Killing PID {pid} on port {port}")
                os.kill(int(pid), signal.SIGKILL)
    except Exception as e:
        print(f"Error killing port {port}: {e}")

def main():
    ports = list(range(40000, 40010)) + list(range(19800, 19810))
    print(f"Cleaning up ports: {ports}")
    for port in ports:
        kill_port(port)
    print("Cleanup complete.")

if __name__ == "__main__":
    main()
