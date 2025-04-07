import structlog
from typing import Any, Dict, Union
import logging
import random
from enum import Enum
from structlog.dev import ConsoleRenderer
from structlog.processors import add_log_level, TimeStamper

class LogTheme(str, Enum):
    """Available logging themes."""
    DEFAULT = "default"
    MATRIX = "matrix"
    POLKADOT = "polkadot"

class ThemeColors:
    """Color palette for different themes."""
    
    # ANSI color codes
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    
    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright foreground colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    
    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"
    
    # Bright background colors
    BG_BRIGHT_BLACK = "\033[100m"
    BG_BRIGHT_RED = "\033[101m"
    BG_BRIGHT_GREEN = "\033[102m"
    BG_BRIGHT_YELLOW = "\033[103m"
    BG_BRIGHT_BLUE = "\033[104m"
    BG_BRIGHT_MAGENTA = "\033[105m"
    BG_BRIGHT_CYAN = "\033[106m"
    BG_BRIGHT_WHITE = "\033[107m"
    
    @classmethod
    def get_theme_palette(cls, theme: LogTheme) -> Dict[str, str]:
        """Get color palette for a specific theme."""
        palettes = {
            LogTheme.DEFAULT: {
                "DEBUG": cls.CYAN,
                "INFO": cls.GREEN,
                "WARNING": cls.YELLOW,
                "ERROR": cls.RED,
                "CRITICAL": cls.MAGENTA,
                "timestamp": cls.BRIGHT_BLACK,
                "logger_name": cls.BLUE,
                "event": cls.WHITE,
            },
            LogTheme.MATRIX: {
                "DEBUG": cls.GREEN,
                "INFO": cls.BRIGHT_GREEN,
                "WARNING": f"{cls.BOLD}{cls.GREEN}",
                "ERROR": f"{cls.BOLD}{cls.BG_BLACK}{cls.GREEN}",
                "CRITICAL": f"{cls.BOLD}{cls.BG_GREEN}{cls.BLACK}",
                "timestamp": cls.GREEN,
                "logger_name": cls.GREEN,
                "event": cls.BRIGHT_GREEN,
            },
            LogTheme.POLKADOT: {
                "DEBUG": cls.MAGENTA,
                "INFO": cls.BRIGHT_MAGENTA,
                "WARNING": f"{cls.BOLD}{cls.MAGENTA}",
                "ERROR": f"{cls.BOLD}{cls.BG_MAGENTA}{cls.WHITE}",
                "CRITICAL": f"{cls.BOLD}{cls.BG_BRIGHT_MAGENTA}{cls.BLACK}",
                "timestamp": cls.BRIGHT_BLACK,
                "logger_name": f"{cls.BOLD}{cls.MAGENTA}",
                "event": cls.WHITE,
            }
        }
        
        return palettes.get(theme, palettes[LogTheme.DEFAULT])

class ThemedConsole(ConsoleRenderer):
    """Console renderer with theme support."""
    
    def __init__(self, theme: Union[LogTheme, str] = LogTheme.DEFAULT):
        super().__init__()
        
        # Convert string to enum if needed
        if isinstance(theme, str):
            try:
                theme = LogTheme(theme.lower())
            except ValueError:
                theme = LogTheme.DEFAULT
        
        self.theme = theme
        self.palette = ThemeColors.get_theme_palette(theme)
        self.reset = ThemeColors.RESET
        
    def get_color(self, key: str) -> str:
        """Get color for a specific key, handling dynamic colors (functions)."""
        color = self.palette.get(key, self.reset)
        if callable(color):
            return color()
        return color
        
    def __call__(self, logger, method_name, event_dict):
        """Render the event with themed colors."""
        # Get the log level from the event dict
        level = event_dict.get("level", "INFO").upper()
        
        # Get the original output from parent class
        output = super().__call__(logger, method_name, event_dict)
        
        # Add colors based on log level
        level_color = self.get_color(level)
        
        # Add extra styling around the timestamp if present
        if "timestamp" in event_dict:
            timestamp_str = str(event_dict["timestamp"])
            timestamp_color = self.get_color("timestamp")
            output = output.replace(
                timestamp_str, 
                f"{timestamp_color}{timestamp_str}{self.reset}"
            )
        
        # Color the logger name if present
        if "logger" in event_dict:
            logger_name = str(event_dict["logger"])
            logger_color = self.get_color("logger_name")
            output = output.replace(
                f"[{logger_name}]", 
                f"[{logger_color}{logger_name}{self.reset}]"
            )
        
        # Apply level color to the level name
        if level in event_dict:
            output = output.replace(
                f"[{level}]", 
                f"[{level_color}{level}{self.reset}]"
            )
        
        # Apply special formatting for specific themes
        if self.theme == LogTheme.MATRIX:
            # Add matrix-like prefixes
            prefix = random.choice(["0x", ">_", ">>", "//", "$_", "#_"])
            output = f"{ThemeColors.GREEN}{prefix} {output}{self.reset}"
        
        return f"{level_color}{output}{self.reset}"


def setup_logging(theme: Union[LogTheme, str] = LogTheme.DEFAULT) -> None:
    """
    Configure structured logging with the specified theme.
    
    Args:
        theme: The color theme to use for logs
    """
    # Convert string to enum if needed
    if isinstance(theme, str):
        try:
            theme = LogTheme(theme.lower())
        except ValueError:
            theme = LogTheme.DEFAULT
        
    structlog.configure(
        processors=[
            add_log_level,
            TimeStamper(fmt="iso"),
            ThemedConsole(theme),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(level=logging.INFO)


def get_logger(name: str) -> Any:
    return structlog.get_logger(name)

logger = get_logger(__name__)