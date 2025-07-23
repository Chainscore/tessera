import logging
import os
import sys
from enum import Enum, auto
from typing import Any, Dict, Final, Mapping, Union

import structlog
from structlog.dev import ConsoleRenderer
from structlog.processors import TimeStamper, add_log_level, JSONRenderer
from structlog.stdlib import LoggerFactory

# ---------- colour palette -------------------------------------------------- #

ESC: Final = "\033["
RESET: Final = f"{ESC}0m"


def _fg(code: int) -> str:
    return f"{ESC}{code}m"


class Colour:
    """Minimal ANSI helpers – keep it small, no colourama dependency."""

    # basic
    BLACK = _fg(30)
    RED = _fg(31)
    GREEN = _fg(32)
    YELLOW = _fg(33)
    BLUE = _fg(34)
    MAGENTA = _fg(35)
    CYAN = _fg(36)
    WHITE = _fg(37)

    # bright
    BBLACK = _fg(90)
    BRED = _fg(91)
    BGREEN = _fg(92)
    BYELLOW = _fg(93)
    BBLUE = _fg(94)
    BMAG = _fg(95)
    BCYAN = _fg(96)
    BWHITE = _fg(97)

    BOLD = f"{ESC}1m"
    UNDER = f"{ESC}4m"


class Theme(str, Enum):
    DEFAULT = auto()
    MATRIX = auto()
    POLKADOT = auto()
    SOLARIZED = auto()
    MONOKAI = auto()
    NOIR = auto()


class Environment(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


_PALETTES: Mapping[Theme, Dict[str, str]] = {
    Theme.DEFAULT: {
        "LEVEL": {  # base colours by level
            "DEBUG": Colour.CYAN,
            "INFO": Colour.GREEN,
            "WARNING": Colour.YELLOW,
            "ERROR": Colour.RED,
            "CRITICAL": Colour.MAGENTA,
        },
        "time": Colour.BBLUE,
        "logger": Colour.BLUE,
        "node": Colour.BMAG,
    },
    Theme.MATRIX: {
        "LEVEL": {
            "DEBUG": Colour.GREEN,
            "INFO": Colour.BGREEN,
            "WARNING": f"{Colour.BOLD}{Colour.GREEN}",
            "ERROR": f"{Colour.BOLD}{Colour.BBLACK}{Colour.GREEN}",
            "CRITICAL": f"{Colour.BOLD}{Colour.BGREEN}{Colour.BLACK}",
        },
        "time": Colour.BBLUE,
        "logger": Colour.GREEN,
        "node": Colour.BGREEN,
        "prefixes": ("0x", ">_", ">>", "//", "$_", "#_"),
    },
    Theme.POLKADOT: {
        "LEVEL": {
            "DEBUG": Colour.MAGENTA,
            "INFO": Colour.BMAG,
            "WARNING": f"{Colour.BOLD}{Colour.MAGENTA}",
            "ERROR": f"{Colour.BOLD}{Colour.BMAG}{Colour.WHITE}",
            "CRITICAL": f"{Colour.BOLD}{Colour.BWHITE}{Colour.BLACK}",
        },
        "time": Colour.BBLUE,
        "logger": f"{Colour.BOLD}{Colour.MAGENTA}",
        "node": f"{Colour.BOLD}{Colour.BMAG}",
    },
    Theme.SOLARIZED: {
        # Approximate Solarized palette
        "LEVEL": {
            "DEBUG": _fg(36),  # base0 blue
            "INFO": _fg(32),  # base1 green
            "WARNING": _fg(33),  # yellow
            "ERROR": _fg(31),  # red
            "CRITICAL": _fg(35),  # magenta
        },
        "time": Colour.BBLUE,  # base01
        "logger": _fg(94),  # cyan
        "node": _fg(96),  # base1 cyan
    },
    Theme.MONOKAI: {
        "LEVEL": {
            "DEBUG": _fg(94),  # blue
            "INFO": _fg(92),  # green
            "WARNING": _fg(93),  # yellow
            "ERROR": _fg(91),  # red
            "CRITICAL": _fg(95),  # magenta
        },
        "time": Colour.BBLUE,
        "logger": _fg(95),
        "node": _fg(92),
    },
    Theme.NOIR: {
        "LEVEL": {
            "DEBUG": Colour.BWHITE,
            "INFO": Colour.WHITE,
            "WARNING": Colour.BRED,
            "ERROR": f"{Colour.BOLD}{Colour.RED}",
            "CRITICAL": f"{Colour.BOLD}{Colour.RED}{Colour.UNDER}",
        },
        "time": Colour.BBLUE,
        "logger": Colour.BWHITE,
        "node": Colour.BRED,
    },
}

# Environment-specific log level defaults
_ENV_LOG_LEVELS = {
    Environment.DEVELOPMENT: logging.DEBUG,
    Environment.TESTING: logging.INFO,
    Environment.PRODUCTION: logging.WARNING,
}


# ---------- renderer -------------------------------------------------------- #


class ThemedRenderer(ConsoleRenderer):
    """structlog ConsoleRenderer with six switchable skins."""

    def __init__(self, theme: Union[Theme, str] = Theme.DEFAULT) -> None:
        super().__init__()
        if isinstance(theme, str):
            theme = Theme[theme.upper()] if theme.upper() in Theme.__members__ else Theme.DEFAULT

        self.theme: Theme = theme
        self.pal: Dict[str, Any] = _PALETTES[self.theme]

    # fast helpers
    def _clr(self, level: str) -> str:
        return self.pal["LEVEL"].get(level, "")

    def __call__(self, logger, method_name, event_dict):
        level = event_dict.pop("level", method_name).upper()  # structlog ensures this
        node = event_dict.pop("node_name", None)
        component = event_dict.pop("component", None)

        # base render first
        msg = super().__call__(logger, method_name, event_dict)

        # assemble final line
        parts: list[str] = []

        if node:
            parts.append(f"{self.pal['node']}[{node + "_" * (10 - (len(node)))}]{RESET}")

        if component:
            parts.append(f"{self.pal['logger']}[{component}]{RESET}")

        # timestamp comes from ConsoleRenderer already; wrap the ISO chunk
        if self.pal.get("time"):
            # naive replace – timestamp is always first token
            ts, rest = msg.split(" ", 1)
            parts.append(f"{self.pal['time']}{ts}{RESET}")
            msg = rest

        # level token
        parts.append(f"{self._clr(level)}[{level}]{RESET}")

        parts.append(msg)  # the rest

        return " ".join(parts)


def filter_sensitive_data(_, __, event_dict):
    """Filter out sensitive data from logs in production."""
    sensitive_keys = {"private_key", "seed", "password", "token", "secret"}

    for key in list(event_dict.keys()):
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            event_dict[key] = "[REDACTED]"

    return event_dict


# ---------- module filtering --------------------------------------------- #


def setup_module_logging_levels():
    """
    Configure different log levels for specific modules.
    """
    # Dict mapping module names to log levels
    module_levels = {}

    for key, value in os.environ.items():
        if key.startswith("LOG_LEVEL_"):
            module_suffix = str(key[10:]).lower()  # Remove "LOG_LEVEL_" prefix
            try:
                level = value.upper()
                print("Log level for", module_suffix, value.upper())
                module_levels[module_suffix] = value.upper()
            except AttributeError:
                logger.warning(f"Invalid log level: {value} for module {module_suffix}")

    for module_name, level in module_levels.items():
        logging.getLogger(module_name).setLevel(level)


# ---------- bootstrap ------------------------------------------------------- #


def setup_logging(
    *,
    theme: Union[Theme, str] = Theme.DEFAULT,
    node_name: str | None = None,
    min_level: int | None = None,
    environment: Union[Environment, str] = Environment.DEVELOPMENT,
    log_file: str | None = None,
    enable_json_logs: bool = False,
) -> None:
    """
    Initialise structlog + stdlib logging with themed console output.

    Args:
        theme: Color theme for console output
        node_name: Name of the node for logging context
        min_level: Minimum log level (if None, uses environment default)
        environment: Runtime environment (development/testing/production)
        log_file: Optional file path for log output
        enable_json_logs: Enable JSON structured logging for production

    Call once at programme start.
    """
    # Normalize environment
    if isinstance(environment, str):
        environment = Environment(environment.lower())

    # Set default log level based on environment
    if min_level is None:
        min_level = _ENV_LOG_LEVELS.get(environment, logging.INFO)

    # silence noisy libs early
    logging.getLogger("quic").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("aioquic").setLevel(logging.WARNING)

    # Configure processors based on environment
    processors = []

    def add_node_context(_, __, event: Dict[str, Any]) -> Dict[str, Any]:
        if node_name:
            event["node_name"] = node_name
        # event["environment"] = environment.value
        return event

    processors.extend(
        [
            add_node_context,
            TimeStamper(fmt="%Y-%m-%d|%H:%M:%S", utc=False),
            add_log_level,
        ]
    )

    # Add sensitive data filtering in production
    if environment == Environment.PRODUCTION:
        processors.insert(-2, filter_sensitive_data)

    # Choose renderer based on environment and configuration
    if enable_json_logs or environment == Environment.PRODUCTION:
        # Use JSON renderer for production or when explicitly requested
        processors.append(JSONRenderer())

        # Set up file logging for production
        if log_file or environment == Environment.PRODUCTION:
            log_file = log_file or f"/var/log/jam/{node_name or 'node'}.log"
            os.makedirs(os.path.dirname(log_file), exist_ok=True)

            # Configure file handler
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(min_level)

            # Also log to stderr in production for container environments
            if environment == Environment.PRODUCTION:
                console_handler = logging.StreamHandler(sys.stderr)
                console_handler.setLevel(logging.WARNING)  # Only warnings+ to console

                # Custom formatter without logger name
                formatter = logging.Formatter("%(message)s")
                file_handler.setFormatter(formatter)
                console_handler.setFormatter(formatter)

                logging.basicConfig(
                    level=min_level,
                    handlers=[file_handler, console_handler],
                    force=True,
                )
            else:
                # Custom formatter without logger name
                formatter = logging.Formatter("%(message)s")
                file_handler.setFormatter(formatter)
                logging.basicConfig(level=min_level, handlers=[file_handler], force=True)
    else:
        # Use themed console renderer for development
        processors.append(ThemedRenderer(theme))

        # Configure console handler with custom formatter that excludes logger name
        console_handler = logging.StreamHandler()
        console_handler.setLevel(min_level)
        formatter = logging.Formatter("%(message)s")
        console_handler.setFormatter(formatter)

        logging.basicConfig(level=min_level, handlers=[console_handler], force=True)

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(min_level),
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Setup module-specific log levels from environment
    setup_module_logging_levels()


def get_logger(name: str | None = None, component: str | None = None):
    """
    Return/ a themed structlog logger with optional component context.

    Args:
        name: Logger name (typically __name__)
        component: Component name for better log organization

    Examples:
        logger = get_logger("pvm")
        logger = get_logger("import")
    """
    logger = structlog.get_logger(name or "jam")
    if component:
        logger = logger.bind(component=component)
    return logger


# Module logger
logger = get_logger("logging")
