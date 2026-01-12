"""
Async TCP client for jamtart telemetry backend.

Handles connection, reconnection, and event transmission.
Follows the jamtart protocol from JIP-3 specification.
"""
import asyncio
import logging
from typing import Optional, List
from dataclasses import dataclass

from tsrkit_types import U8, U16, U32, U64, String, Bytes
from jam.utils.constants import PARAMS_ENCODED, C

from .events import Event, Status, SyncStatusChanged

logger = logging.getLogger("node")


@dataclass
class TelemetryConfig:
    """Configuration for telemetry client"""
    host: str = "localhost"
    port: int = 9000
    node_name: str = "tessera-node"
    node_version: str = "0.1.0"
    reconnect_delay: float = 5.0
    batch_size: int = 100
    batch_timeout: float = 1.0


class TelemetryClient:
    """
    Async TCP client for jamtart telemetry.
    
    Sends NodeInformation on connect, then streams events.
    """
    
    _instance: Optional["TelemetryClient"] = None
    
    def __init__(self, config: TelemetryConfig):
        self.config = config
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._connected = False
        self._event_queue: asyncio.Queue = asyncio.Queue(maxsize=10000)
        self._running = False
        self._send_task: Optional[asyncio.Task] = None
        self._peer_id: Optional[bytes] = None
        self._genesis_hash: Optional[bytes] = None
        
    @classmethod
    def get_instance(cls) -> Optional["TelemetryClient"]:
        """Get the singleton instance"""
        return cls._instance
    
    @classmethod
    def setup(cls, config: TelemetryConfig) -> "TelemetryClient":
        """Setup the singleton instance"""
        cls._instance = cls(config)
        return cls._instance
    
    def set_node_identity(self, peer_id: bytes, genesis_hash: bytes):
        """Set the node's peer ID and genesis hash for handshake"""
        self._peer_id = peer_id
        self._genesis_hash = genesis_hash
    
    @property
    def is_connected(self) -> bool:
        return self._connected
        
    def _build_handshake(self) -> bytes:
        """Build the NodeInformation message"""
        # Default values if not set
        peer_id = self._peer_id or bytes(32)
        genesis_hash = self._genesis_hash or bytes(32)
        
        # Peer Address (16 bytes IP + 2 bytes port)
        # For now, just sending 0 (unspecified)
        peer_address = bytes(16) + U16(0).encode()
        
        node_flags = U32(1) # Bit 0: PVM recompiler (assuming yes for now)
        
        # 0 (Single byte, telemetry protocol version)
        handshake = U8(0).encode()
        handshake += PARAMS_ENCODED
        handshake += genesis_hash
        handshake += peer_id
        handshake += peer_address
        handshake += node_flags.encode()
        handshake += String(self.config.node_name).encode()
        handshake += String(self.config.node_version).encode() # Version
        handshake += String("0.7.1").encode() # Gray Paper version
        handshake += String("tessera node").encode() # Note
        
        return handshake
    
    async def connect(self) -> bool:
        """Connect to the jamtart backend."""
        try:
            logger.info(
                f"Connecting to telemetry backend {self.config.host}:{self.config.port}"
            )
            
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.config.host, self.config.port),
                timeout=10.0
            )
            
            # Send NodeInformation handshake with length prefix
            handshake = self._build_handshake()
            
            # All messages need a 4-byte LE length prefix
            length_bytes = len(handshake).to_bytes(4, byteorder='little')
            
            self._writer.write(length_bytes + handshake)
            await self._writer.drain()
            
            self._connected = True
            logger.info("Connected to telemetry backend")
            return True
            
        except asyncio.TimeoutError:
            logger.warning("Telemetry connection timed out")
            return False
        except ConnectionRefusedError:
            logger.warning("Telemetry connection refused")
            return False
        except Exception as e:
            logger.error(f"Telemetry connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the backend"""
        self._running = False
        self._connected = False
        
        if self._send_task:
            self._send_task.cancel()
            try:
                await self._send_task
            except asyncio.CancelledError:
                pass
        
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass
            self._writer = None
            self._reader = None
            
        logger.info("Disconnected from telemetry backend")
    
    async def run(self):
        """
        Main run loop - maintains connection and sends events.
        """
        self._running = True
        
        while self._running:
            # Connect if needed
            if not self._connected:
                if await self.connect():
                    self._send_task = asyncio.create_task(self._send_loop())
                else:
                    await asyncio.sleep(self.config.reconnect_delay)
                    continue
            
            # Wait for disconnect or stop
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
    
    async def _send_loop(self):
        """Background task to send queued events"""
        batch = []
        
        while self._connected and self._running:
            try:
                # Wait for event with timeout
                try:
                    event = await asyncio.wait_for(
                        self._event_queue.get(),
                        timeout=self.config.batch_timeout
                    )
                    batch.append(event)
                except asyncio.TimeoutError:
                    pass
                
                # Send batch if we have events or batch is full
                if batch and (len(batch) >= self.config.batch_size or 
                              self._event_queue.empty()):
                    await self._send_batch(batch)
                    batch = []
                    
            except asyncio.CancelledError:
                # Send remaining events before exit
                if batch:
                    await self._send_batch(batch)
                raise
            except Exception as e:
                logger.error(f"Error in send loop: {e}")
                self._connected = False
                break
    
    async def _send_batch(self, batch: list[bytes]):
        """Send a batch of encoded events"""
        if not self._writer:
            return
            
        try:
            for event_data in batch:
                self._writer.write(event_data)
            await self._writer.drain()
        except Exception as e:
            logger.error(f"Failed to send events: {e}")
            self._connected = False
    
    def send_raw(self, data: bytes):
        """
        Queue raw bytes for sending (non-blocking).
        """
        try:
            self._event_queue.put_nowait(data)
        except asyncio.QueueFull:
            logger.warning("Telemetry queue full, dropping event")
    
    def send_status(
        self,
        num_peers: int = 0,
        num_val_peers: int = 0,
        num_block_announcement_peers: int = 0, # Changed name to match Event
        guarantees_by_core: List[int] = None,   # Changed type hint
        num_shards: int = 0,
        shards_size: int = 0,
        num_preimages: int = 0,
        preimages_size: int = 0,
    ):
        """Send Status event (type 10)"""
        if guarantees_by_core is None:
            guarantees_by_core = []
            
        # Ensure guarantees_by_core is proper Bytes(C) type
        if isinstance(guarantees_by_core, list):
            data = bytes(guarantees_by_core)
        elif isinstance(guarantees_by_core, bytes):
            data = guarantees_by_core
        else:
            data = bytes(C)
            
        # Pad or truncate to C
        if len(data) < C:
            data += bytes(C - len(data))
        elif len(data) > C:
            data = data[:C]
            
        guarantees_val = Bytes(data)
        
        event = Status(
            num_peers=U32(num_peers),
            num_validator_peers=U32(num_val_peers),
            num_block_announcement_peers=U32(num_block_announcement_peers),
            guarantees_by_core=guarantees_val,
            num_shards=U32(num_shards),
            shards_size=U64(shards_size),
            num_preimages=U32(num_preimages),
            preimages_size=U32(preimages_size)
        )
        self.send_raw(event.encode())
    
    def send_sync_status_changed(self, synced: bool):
        """Send SyncStatusChanged event (type 13)"""
        self.send_raw(SyncStatusChanged(synced=synced).encode())


# Global client accessor
def get_client() -> Optional[TelemetryClient]:
    """Get the global telemetry client"""
    return TelemetryClient.get_instance()


from datetime import datetime, timezone
from tsrkit_types import U64, U8
from jam.utils.constants import JCE_EPOCH

def emit_event(event: Event):
    """Emit a telemetry event"""
    client = get_client()
    if client:
        # Calculate timestamp: Microseconds since JCE_EPOCH
        now = datetime.now(timezone.utc)
        delta = now - JCE_EPOCH
        timestamp_us = int(delta.total_seconds() * 1_000_000)
        
        discriminator_val = int(event.DISCRIMINATOR)
        if discriminator_val == 255:
            logger.error(f"Event {type(event).__name__} has no DISCRIMINATOR defined")
            return

        # Content = Timestamp ++ Discriminator ++ Data
        content = U64(timestamp_us).encode() + U8(discriminator_val).encode() + event.encode()
        
        length = len(content)
        # 4 bytes for length (Little Endian)
        length_bytes = length.to_bytes(4, byteorder='little')
        
        client.send_raw(length_bytes + content)

