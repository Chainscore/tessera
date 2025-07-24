import asyncio
import os
from pathlib import Path
import signal
from jam.logging import get_logger

# Logger for Node test
logger = get_logger("test")

proc = None

async def run_pj_command(node_id: int):
    global proc
    binary_path = str(Path(__file__).parents[3] / "polkajam")
    envs = ""
    if hasattr(os.environ, "RUST_LOG"):
        envs = f"RUST_LOG={os.environ["RUST_LOG"]}"

    command = f"export {envs} && exec {binary_path}/polkajam run --dev-validator {node_id} --temp --rpc-port {19800+int(node_id)}"

    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        async def log_stream(stream, stream_name):
            while True:
                line = await stream.readline()
                if not line:
                    break
                print(f"[{node_id}] {line.decode().strip()}")

        # Wait for the process to finish and for the loggers to finish
        await asyncio.gather(
            log_stream(proc.stdout, "stdout"),
            log_stream(proc.stderr, "stderr"),
        )
        
        await proc.wait()

        if proc.returncode == 0:
            print(f"[{node_id}] Command '{command}' exited successfully.")
        elif proc.returncode < 0:
            print(f"[{node_id}] Command terminated by signal {-proc.returncode}.")
        else:
            print(f"[{node_id}] Command '{command}' failed with exit code {proc.returncode}.")
    except Exception as e:
        print(f"[{node_id}] Error running command '{command}': {e}")

def run_polkajam(name: str, val_index: int):
    # Handle clean termination
    def handle_sigterm(signum, frame):
        if proc:
            proc.terminate()

    signal.signal(signal.SIGTERM, handle_sigterm)

    asyncio.run(run_pj_command(val_index))
