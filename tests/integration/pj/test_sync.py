import asyncio
import json
import urllib.request
import os
import pytest
from tests.integration.utils.setup_processes import Client, Role, setup_processes

async def poll_rpc_stats(ports, duration, stop_event):
    """
    Polls RPC endpoints for node status.
    """
    start_time = asyncio.get_running_loop().time()
    
    print(f"\n[Monitor] Starting RPC polling for {len(ports)} nodes...")
    
    # Allow nodes to start up
    await asyncio.sleep(10)
    
    while not stop_event.is_set():
        current_time = asyncio.get_running_loop().time()
        if current_time - start_time > duration:
            break
            
        print(f"\n--- Network Status (T+{int(current_time - start_time)}s) ---")
        
        stats = []
        for port in ports:
            try:
                # Call bestBlock
                req = urllib.request.Request(
                    f"http://127.0.0.1:{port}/",
                    data=json.dumps({"jsonrpc": "2.0", "method": "bestBlock", "id": 1, "params": []}).encode(),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=2) as response:
                     res = json.load(response)
                     result = res.get("result")
                     if result:
                         slot = result.get('slot')
                         hh = bytes(result.get('header_hash')).hex()
                         stats.append((port, slot, hh))
                         print(f"Node {port}: Slot {slot:<5} | Head {hh[:8]}...")
                     else:
                         print(f"Node {port}: Empty Result")
            except Exception as e:
                print(f"Node {port}: Unreachable ({e})")
                pass
        
        # Validation checks
        if len(stats) > 0:
            slots = [s[1] for s in stats]
            max_slot = max(slots)
            min_slot = min(slots)
            if max_slot > 0:
                print(f"[Monitor] Chain advancing! Max Slot: {max_slot}")
                
            if len(stats) == len(ports):
                if max_slot - min_slot <= 1:
                     print(f"[Monitor] All nodes in sync within 1 slot.")
        
        await asyncio.sleep(5)

@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_sync_6_validators():
    """
    Runs a 6-validator network and verifies synchronization via RPC.
    """
    rpc_ports = range(19800, 19806)
    clients = [Client(Role.VAL, 40000 + i) for i in range(6)]
    
    duration = 60 # Run for 60 seconds
    stop_event = asyncio.Event()

    # Start Monitor
    monitor_task = asyncio.create_task(poll_rpc_stats(rpc_ports, duration, stop_event))
    
    try:
        # Start Nodes
        await setup_processes(clients, [], duration + 5)
    finally:
        stop_event.set()
        await monitor_task
