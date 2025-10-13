"""
Simple, reliable logging system for JAM using structlog
"""
import logging
import os
import sys
from datetime import datetime
from enum import Enum
from typing import Optional

import structlog
import logging.config
from .themes import get_theme_colors, RESET


class LogModule(Enum):
    """Enum for configurable log modules"""
    NODE = "node"
    NETWORK = "network"
    BLOCK = "block"
    PVM = "pvm"


# Global settings
_theme_colors = get_theme_colors("default")
_node_name: Optional[str] = None
_is_setup = False

class ColoredRenderer:
    """Simple colored renderer for structlog"""

    def __call__(self, logger, name, event_dict):
        # Get timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Get colors
        level = event_dict.get("level", "INFO").upper()
        level_color = _theme_colors.get(level, "")
        node_color = _theme_colors.get("node", "")

        # Build parts
        parts = []

        # Add node name if set
        if _node_name:
            parts.append(f"{node_color}[{_node_name:9}]{RESET}")
        else:
            parts.append(" " * 11)

        # Add timestamp
        parts.append(f"{timestamp}")

        # Add level
        parts.append(f"{level_color}[{level:<7}]{RESET}")

        # Add logger name if not "jam"
        logger_name = event_dict.get("logger", "jam")
        if logger_name != "jam":
            parts.append(f"[{logger_name}]")

        # Add message
        parts.append(event_dict.get("event", ""))

        # Add structured fields
        extras = {k: v for k, v in event_dict.items() if k not in ["event", "level", "timestamp", "logger"]}
        if extras:
            parts.append(f" | {extras}")

        return " ".join(parts)

def add_node_name(logger, method_name, event_dict):
    if _node_name:
        event_dict["node"] = _node_name
    return event_dict

def setup_logging(theme: str = "default", node_name: Optional[str] = None):
    """
    Setup logging system - call once at startup
    
    Args:
        theme: Color theme name
        node_name: Node identifier for logs
    """
    global _theme_colors, _node_name, _is_setup
    
    _theme_colors = get_theme_colors(theme)
    _node_name = node_name
    _is_setup = True
    
    # Get root log level from env
    root_level_name = os.environ.get("JAM_LOG_LEVEL", "CRITICAL").upper()
    root_level = getattr(logging, root_level_name, logging.CRITICAL)
    
    # Collect module levels
    module_levels = {}
    for key, value in os.environ.items():
        if key.startswith("JAM_LOG_LEVEL_"):
            module_name = key[14:]
            try:
                module = LogModule[module_name.upper()]
                level = getattr(logging, value.upper(), logging.CRITICAL)
                module_levels[module.value] = level
            except (KeyError, AttributeError):
                # Invalid module or level, ignore
                pass
    
    # Find minimum level for wrapper
    all_levels = [root_level] + list(module_levels.values())
    min_level = min(all_levels)

    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)

    # Configure logging with two handlers: stream and file
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "default": {
                "level": min_level,
                "class": "logging.StreamHandler",
                "formatter": "colored",
            },
            "file": {
                "level": min_level,
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/app.log",
                "formatter": "json",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 7,
            },
        },
        "formatters": {
            "colored": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": ColoredRenderer(),
                "foreign_pre_chain": [
                    structlog.stdlib.add_log_level,
                    add_node_name,
                    structlog.processors.TimeStamper(fmt="%H:%M:%S"),
                ],
            },
            "json": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.processors.JSONRenderer(),
                "foreign_pre_chain": [
                    structlog.stdlib.add_log_level,
                    add_node_name,
                    structlog.processors.TimeStamper(fmt="%H:%M:%S"),
                ],
            },
        },
        "loggers": {
            "": {
                "handlers": ["default", "file"],
                "level": "DEBUG",
                "propagate": True,
            },
        },
    })

    for module, level in module_levels.items():
        logging.getLogger(module).setLevel(level)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            add_node_name,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%H:%M:%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(min_level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Silence noisy libraries
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("quic").setLevel(logging.WARNING)
    logging.getLogger("aioquic").setLevel(logging.WARNING)


# Pre-configured loggers for main components
node_logger = structlog.get_logger("node")
network_logger = structlog.get_logger("network")
block_logger = structlog.get_logger("block")
pvm_logger = structlog.get_logger("pvm")

# Default logger
logger = structlog.get_logger("jam")

def get_logger(name: str = "jam"):
    """Get a logger by name"""
    return structlog.get_logger(name)
