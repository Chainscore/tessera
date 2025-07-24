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


def _bg(code: int) -> str:
    return f"{ESC}{code + 10}m"


def _rgb(r: int, g: int, b: int) -> str:
    """24-bit RGB color support"""
    return f"{ESC}38;2;{r};{g};{b}m"


def _rgb_bg(r: int, g: int, b: int) -> str:
    """24-bit RGB background color support"""
    return f"{ESC}48;2;{r};{g};{b}m"


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

    # Text effects
    BOLD = f"{ESC}1m"
    DIM = f"{ESC}2m"
    ITALIC = f"{ESC}3m"
    UNDER = f"{ESC}4m"
    BLINK = f"{ESC}5m"
    REVERSE = f"{ESC}7m"
    STRIKE = f"{ESC}9m"

    # 256 color palette shortcuts (most common/useful colors)
    ORANGE = _fg(208)
    PURPLE = _fg(129)
    PINK = _fg(205)
    LIME = _fg(154)
    TEAL = _fg(80)
    NAVY = _fg(17)
    MAROON = _fg(88)
    OLIVE = _fg(100)
    CORAL = _fg(203)
    GOLD = _fg(220)
    SILVER = _fg(188)
    INDIGO = _fg(54)
    VIOLET = _fg(99)
    TURQUOISE = _fg(80)
    SALMON = _fg(209)
    KHAKI = _fg(143)

    # RGB Colors (24-bit true color)
    NEON_GREEN = _rgb(57, 255, 20)
    NEON_BLUE = _rgb(77, 77, 255)
    NEON_PINK = _rgb(255, 20, 147)
    ELECTRIC_CYAN = _rgb(0, 255, 255)
    HOT_MAGENTA = _rgb(255, 0, 255)
    FIRE_RED = _rgb(255, 69, 0)
    DEEP_PURPLE = _rgb(148, 0, 211)
    FOREST_GREEN = _rgb(34, 139, 34)
    SUNSET_ORANGE = _rgb(255, 165, 0)
    ROYAL_BLUE = _rgb(65, 105, 225)


class Theme(str, Enum):
    DEFAULT = auto()
    MATRIX = auto()
    POLKADOT = auto()
    SOLARIZED = auto()
    MONOKAI = auto()
    NOIR = auto()

    CYBERPUNK = auto()
    OCEAN = auto()
    SUNSET = auto()
    FOREST = auto()
    NEON = auto()
    RETRO = auto()
    MINIMAL = auto()
    HACKER = auto()
    RAINBOW = auto()
    TERMINAL_GREEN = auto()
    DRACULA = auto()
    GRUVBOX = auto()
    NORD = auto()
    TOKYO_NIGHT = auto()
    ONE_DARK = auto()
    PASTEL = auto()
    HIGH_CONTRAST = auto()
    GITHUB = auto()
    VS_CODE = auto()


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
    Theme.CYBERPUNK: {
        "LEVEL": {
            "DEBUG": Colour.NEON_BLUE,
            "INFO": Colour.ELECTRIC_CYAN,
            "WARNING": Colour.NEON_PINK,
            "ERROR": Colour.FIRE_RED,
            "CRITICAL": f"{Colour.BOLD}{Colour.HOT_MAGENTA}{Colour.BLINK}",
        },
        "time": Colour.PURPLE,
        "logger": Colour.NEON_GREEN,
        "node": Colour.ELECTRIC_CYAN,
        "prefixes": (">>", "0x", "//", ">>>", "@_", "#!"),
    },
    Theme.OCEAN: {
        "LEVEL": {
            "DEBUG": Colour.TEAL,
            "INFO": Colour.CYAN,
            "WARNING": Colour.TURQUOISE,
            "ERROR": Colour.CORAL,
            "CRITICAL": f"{Colour.BOLD}{Colour.RED}",
        },
        "time": Colour.ROYAL_BLUE,
        "logger": Colour.NAVY,
        "node": Colour.BCYAN,
    },
    Theme.SUNSET: {
        "LEVEL": {
            "DEBUG": Colour.GOLD,
            "INFO": Colour.SUNSET_ORANGE,
            "WARNING": Colour.CORAL,
            "ERROR": Colour.FIRE_RED,
            "CRITICAL": f"{Colour.BOLD}{Colour.MAROON}",
        },
        "time": Colour.PINK,
        "logger": Colour.ORANGE,
        "node": Colour.SALMON,
    },
    Theme.FOREST: {
        "LEVEL": {
            "DEBUG": Colour.FOREST_GREEN,
            "INFO": Colour.LIME,
            "WARNING": Colour.KHAKI,
            "ERROR": Colour.MAROON,
            "CRITICAL": f"{Colour.BOLD}{Colour.RED}",
        },
        "time": Colour.OLIVE,
        "logger": Colour.GREEN,
        "node": Colour.BGREEN,
    },
    Theme.NEON: {
        "LEVEL": {
            "DEBUG": f"{Colour.BOLD}{Colour.NEON_BLUE}",
            "INFO": f"{Colour.BOLD}{Colour.NEON_GREEN}",
            "WARNING": f"{Colour.BOLD}{Colour.NEON_PINK}",
            "ERROR": f"{Colour.BOLD}{Colour.FIRE_RED}{Colour.BLINK}",
            "CRITICAL": f"{Colour.BOLD}{Colour.HOT_MAGENTA}{Colour.REVERSE}",
        },
        "time": f"{Colour.BOLD}{Colour.ELECTRIC_CYAN}",
        "logger": f"{Colour.BOLD}{Colour.NEON_GREEN}",
        "node": f"{Colour.BOLD}{Colour.NEON_PINK}",
    },
    Theme.RETRO: {
        "LEVEL": {
            "DEBUG": _fg(94),  # bright blue
            "INFO": _fg(46),  # bright green
            "WARNING": _fg(226),  # bright yellow
            "ERROR": _fg(196),  # bright red
            "CRITICAL": f"{Colour.BOLD}{_fg(201)}",  # bright magenta
        },
        "time": _fg(39),  # bright cyan
        "logger": _fg(208),  # orange
        "node": _fg(165),  # magenta
    },
    Theme.MINIMAL: {
        "LEVEL": {
            "DEBUG": Colour.DIM + Colour.WHITE,
            "INFO": Colour.WHITE,
            "WARNING": f"{Colour.BOLD}{Colour.WHITE}",
            "ERROR": f"{Colour.BOLD}{Colour.BWHITE}",
            "CRITICAL": f"{Colour.BOLD}{Colour.BWHITE}{Colour.UNDER}",
        },
        "time": Colour.DIM + Colour.WHITE,
        "logger": Colour.WHITE,
        "node": f"{Colour.BOLD}{Colour.WHITE}",
    },
    Theme.HACKER: {
        "LEVEL": {
            "DEBUG": Colour.DIM + Colour.GREEN,
            "INFO": Colour.GREEN,
            "WARNING": f"{Colour.BOLD}{Colour.YELLOW}",
            "ERROR": f"{Colour.BOLD}{Colour.RED}",
            "CRITICAL": f"{Colour.BOLD}{Colour.RED}{Colour.REVERSE}",
        },
        "time": Colour.DIM + Colour.GREEN,
        "logger": f"{Colour.BOLD}{Colour.GREEN}",
        "node": f"{Colour.BOLD}{Colour.BGREEN}",
        "prefixes": ("$", ">>", "0x", "#", "//", ">>>"),
    },
    Theme.RAINBOW: {
        "LEVEL": {
            "DEBUG": Colour.VIOLET,
            "INFO": Colour.BLUE,
            "WARNING": Colour.YELLOW,
            "ERROR": Colour.ORANGE,
            "CRITICAL": f"{Colour.BOLD}{Colour.RED}",
        },
        "time": Colour.INDIGO,
        "logger": Colour.GREEN,
        "node": Colour.CYAN,
    },
    Theme.TERMINAL_GREEN: {
        "LEVEL": {
            "DEBUG": f"{Colour.DIM}{Colour.GREEN}",
            "INFO": Colour.GREEN,
            "WARNING": f"{Colour.BOLD}{Colour.GREEN}",
            "ERROR": f"{Colour.BOLD}{Colour.BGREEN}",
            "CRITICAL": f"{Colour.BOLD}{Colour.BGREEN}{Colour.REVERSE}",
        },
        "time": f"{Colour.DIM}{Colour.GREEN}",
        "logger": Colour.GREEN,
        "node": f"{Colour.BOLD}{Colour.GREEN}",
        "prefixes": (">", ">>", "$", "#", "//"),
    },
    Theme.DRACULA: {
        "LEVEL": {
            "DEBUG": _rgb(139, 233, 253),  # cyan
            "INFO": _rgb(80, 250, 123),  # green
            "WARNING": _rgb(241, 250, 140),  # yellow
            "ERROR": _rgb(255, 85, 85),  # red
            "CRITICAL": f"{Colour.BOLD}{_rgb(255, 121, 198)}",  # pink
        },
        "time": _rgb(189, 147, 249),  # purple
        "logger": _rgb(248, 248, 242),  # foreground
        "node": _rgb(80, 250, 123),  # green
    },
    Theme.GRUVBOX: {
        "LEVEL": {
            "DEBUG": _rgb(131, 165, 152),  # aqua
            "INFO": _rgb(184, 187, 38),  # yellow
            "WARNING": _rgb(254, 128, 25),  # orange
            "ERROR": _rgb(251, 73, 52),  # red
            "CRITICAL": f"{Colour.BOLD}{_rgb(211, 134, 155)}",  # purple
        },
        "time": _rgb(146, 131, 116),  # gray
        "logger": _rgb(235, 219, 178),  # fg
        "node": _rgb(142, 192, 124),  # green
    },
    Theme.NORD: {
        "LEVEL": {
            "DEBUG": _rgb(143, 188, 187),  # frost
            "INFO": _rgb(163, 190, 140),  # aurora green
            "WARNING": _rgb(235, 203, 139),  # aurora yellow
            "ERROR": _rgb(191, 97, 106),  # aurora red
            "CRITICAL": f"{Colour.BOLD}{_rgb(180, 142, 173)}",  # aurora purple
        },
        "time": _rgb(129, 161, 193),  # frost blue
        "logger": _rgb(236, 239, 244),  # snow storm
        "node": _rgb(136, 192, 208),  # frost
    },
    Theme.TOKYO_NIGHT: {
        "LEVEL": {
            "DEBUG": _rgb(125, 207, 255),  # blue
            "INFO": _rgb(158, 206, 106),  # green
            "WARNING": _rgb(224, 175, 104),  # yellow
            "ERROR": _rgb(247, 118, 142),  # red
            "CRITICAL": f"{Colour.BOLD}{_rgb(187, 154, 247)}",  # purple
        },
        "time": _rgb(86, 95, 137),  # comment
        "logger": _rgb(192, 202, 245),  # fg
        "node": _rgb(122, 162, 247),  # blue
    },
    Theme.ONE_DARK: {
        "LEVEL": {
            "DEBUG": _rgb(97, 175, 239),  # blue
            "INFO": _rgb(152, 195, 121),  # green
            "WARNING": _rgb(229, 192, 123),  # yellow
            "ERROR": _rgb(224, 108, 117),  # red
            "CRITICAL": f"{Colour.BOLD}{_rgb(198, 120, 221)}",  # purple
        },
        "time": _rgb(92, 99, 112),  # comment
        "logger": _rgb(171, 178, 191),  # fg
        "node": _rgb(86, 182, 194),  # cyan
    },
    Theme.PASTEL: {
        "LEVEL": {
            "DEBUG": _rgb(179, 205, 230),  # pastel blue
            "INFO": _rgb(195, 231, 195),  # pastel green
            "WARNING": _rgb(255, 230, 179),  # pastel orange
            "ERROR": _rgb(255, 179, 179),  # pastel red
            "CRITICAL": f"{Colour.BOLD}{_rgb(230, 179, 255)}",  # pastel purple
        },
        "time": _rgb(204, 204, 255),  # pastel lavender
        "logger": _rgb(128, 128, 128),  # gray
        "node": _rgb(255, 204, 229),  # pastel pink
    },
    Theme.HIGH_CONTRAST: {
        "LEVEL": {
            "DEBUG": f"{Colour.BOLD}{Colour.BWHITE}",
            "INFO": f"{Colour.BOLD}{Colour.WHITE}",
            "WARNING": f"{Colour.BOLD}{Colour.BYELLOW}{Colour.BBLACK}",
            "ERROR": f"{Colour.BOLD}{Colour.BWHITE}{Colour.BRED}",
            "CRITICAL": f"{Colour.BOLD}{Colour.BYELLOW}{Colour.BRED}{Colour.BLINK}",
        },
        "time": f"{Colour.BOLD}{Colour.BCYAN}",
        "logger": f"{Colour.BOLD}{Colour.BWHITE}",
        "node": f"{Colour.BOLD}{Colour.BGREEN}",
    },
    Theme.GITHUB: {
        "LEVEL": {
            "DEBUG": _rgb(88, 166, 255),  # blue
            "INFO": _rgb(46, 160, 67),  # green
            "WARNING": _rgb(251, 188, 5),  # yellow
            "ERROR": _rgb(248, 81, 73),  # red
            "CRITICAL": f"{Colour.BOLD}{_rgb(163, 113, 247)}",  # purple
        },
        "time": _rgb(139, 148, 158),  # gray
        "logger": _rgb(36, 41, 47),  # fg dark
        "node": _rgb(9, 105, 218),  # blue
    },
    Theme.VS_CODE: {
        "LEVEL": {
            "DEBUG": _rgb(86, 156, 214),  # blue
            "INFO": _rgb(78, 201, 176),  # teal
            "WARNING": _rgb(220, 220, 170),  # yellow
            "ERROR": _rgb(244, 71, 71),  # red
            "CRITICAL": f"{Colour.BOLD}{_rgb(197, 134, 192)}",  # pink
        },
        "time": _rgb(106, 153, 85),  # comment green
        "logger": _rgb(212, 212, 212),  # fg
        "node": _rgb(79, 193, 255),  # light blue
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
            theme = (
                Theme[theme.upper()]
                if theme.upper() in Theme.__members__
                else Theme.DEFAULT
            )

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
            parts.append(f"{self.pal['node']}[{node}]{RESET}")

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
    logger.warning("⚠ Make sure to check which log modules you want to see!")
    for key, value in os.environ.items():
        if key.startswith("LOG_LEVEL_"):
            module_suffix = str(key[10:]).lower()  # Remove "LOG_LEVEL_" prefix
            try:
                level = value.upper()
                # print("Log level for", module_suffix, value.upper())
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
                logging.basicConfig(
                    level=min_level, handlers=[file_handler], force=True
                )
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
