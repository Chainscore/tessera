# TODO: Work in Progress

import os
import pytest
import asyncio
import subprocess

clients = [40000, 40001]


TMUX_SESSION_NAME = "jam_test_nodes"

def create_tmux_windows_for_nodes():
    # Create tmux session with one window and two panes
    subprocess.run(["tmux", "new", "-d", "-s", TMUX_SESSION_NAME, "-n", "jam_nodes"])
    subprocess.run(["tmux", "split-window", "-h", "-t", f"{TMUX_SESSION_NAME}:0"])

    # Build Poetry + Python node runner commands
    cmd_40000 = (
        "poetry run python ./tests/integration/genesis/run_node.py "
        "--env envs/40000.env "
        "--theme matrix "
        "--is-validator"
)
    cmd_40001 = (
        "poetry run python ./tests/integration/genesis/run_node.py "
        "--env envs/40001.env "
        "--theme polkadot "
        "--is-validator"
    )

    # Send to tmux panes
    subprocess.run(["tmux", "send-keys", "-t", f"{TMUX_SESSION_NAME}:0.0", cmd_40000, "Enter"])
    subprocess.run(["tmux", "send-keys", "-t", f"{TMUX_SESSION_NAME}:0.1", cmd_40001, "Enter"])

    # TODO: Fix this. For now run this command in separate terminal window.
    subprocess.Popen(["gnome-shell", "--", "tmux", "attach", "-t", TMUX_SESSION_NAME])

@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_connection():
    print("[+] Starting JAM nodes in tmux panes...")

    create_tmux_windows_for_nodes()

    print("[+] Tmux panes ready. Attach with:")
    print(f"    tmux attach -t {TMUX_SESSION_NAME}")
    print("[+] Running for 40 seconds while nodes initialize and handshake...")

    await asyncio.sleep(40)

    print("[+] Test complete, cleaning up tmux session...")
    subprocess.run(["tmux", "kill-session", "-t", TMUX_SESSION_NAME])
    print("[+] Tmux session cleaned. Test finished.")

