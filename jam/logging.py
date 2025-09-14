"""
Simple, reliable logging system for JAM
"""
import logging
import sys
from datetime import datetime
from typing import Optional

from .themes import get_theme_colors, RESET

# Global settings
_theme_colors = get_theme_colors("default")
_node_name: Optional[str] = None
_is_setup = False


class ColoredFormatter(logging.Formatter):
    """Simple colored formatter"""
    
    def format(self, record):
        # Get timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Get colors for this level
        level_color = _theme_colors.get(record.levelname, "")
        node_color = _theme_colors.get("node", "")
        
        # Build message parts
        parts = []
        
        # Add node name if set
        if _node_name:
            parts.append(f"{node_color}[{_node_name}]{RESET}")
        
        # Add timestamp
        parts.append(f"{timestamp}")
        
        # Add level
        parts.append(f"{level_color}[{record.levelname}]{RESET}")
        
        # Add logger name if not "jam"
        if record.name != "jam":
            parts.append(f"[{record.name}]")
        
        # Add message
        parts.append(record.getMessage())
        
        return " ".join(parts)


def setup_logging(theme: str = "default", node_name: Optional[str] = None, level: str = "INFO"):
    """
    Setup logging system - call once at startup
    
    Args:
        theme: Color theme name
        node_name: Node identifier for logs
        level: Log level (DEBUG, INFO, WARNING, ERROR)
    """
    global _theme_colors, _node_name, _is_setup
    
    _theme_colors = get_theme_colors(theme)
    _node_name = node_name
    _is_setup = True
    
    # Remove existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Setup console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColoredFormatter())
    
    # Configure root logger
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.addHandler(handler)
    
    # Silence noisy libraries
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("quic").setLevel(logging.WARNING)
    logging.getLogger("aioquic").setLevel(logging.WARNING)


# Pre-configured loggers for main components
network_logger = logging.getLogger("network")
state_logger = logging.getLogger("state")
block_logger = logging.getLogger("block")
consensus_logger = logging.getLogger("consensus")
api_logger = logging.getLogger("api")

# Default logger
logger = logging.getLogger("jam")


def get_logger(name: str = "jam") -> logging.Logger:
    """Get a logger by name"""
    return logging.getLogger(name)
