"""
Theme definitions for console output
"""
from typing import Dict, Final

# ANSI color codes
ESC: Final = "\033["
RESET: Final = f"{ESC}0m"

def _fg(code: int) -> str:
    return f"{ESC}{code}m"

def _rgb(r: int, g: int, b: int) -> str:
    return f"{ESC}38;2;{r};{g};{b}m"

class Colors:
    # Basic colors
    BLACK = _fg(30)
    RED = _fg(31)
    GREEN = _fg(32)
    YELLOW = _fg(33)
    BLUE = _fg(34)
    MAGENTA = _fg(35)
    CYAN = _fg(36)
    WHITE = _fg(37)
    
    # Bright colors
    BRED = _fg(91)
    BGREEN = _fg(92)
    BYELLOW = _fg(93)
    BBLUE = _fg(94)
    BMAG = _fg(95)
    BCYAN = _fg(96)
    BWHITE = _fg(97)
    
    # Effects
    BOLD = f"{ESC}1m"
    DIM = f"{ESC}2m"

# Theme configurations
THEMES: Dict[str, Dict[str, str]] = {
    "default": {
        "TRACE": Colors.DIM,
        "DEBUG": Colors.CYAN,
        "INFO": Colors.GREEN,
        "WARNING": Colors.YELLOW,
        "ERROR": Colors.RED,
        "CRITICAL": Colors.MAGENTA,
        "node": Colors.BMAG,
    },
    "ocean": {
        "TRACE": Colors.DIM,
        "DEBUG": Colors.CYAN,
        "INFO": Colors.BCYAN,
        "WARNING": Colors.YELLOW,
        "ERROR": Colors.RED,
        "CRITICAL": Colors.BRED,
        "node": Colors.BBLUE,
    },
    "forest": {
        "TRACE": Colors.DIM,
        "DEBUG": Colors.GREEN,
        "INFO": Colors.BGREEN,
        "WARNING": Colors.YELLOW,
        "ERROR": Colors.RED,
        "CRITICAL": Colors.BRED,
        "node": Colors.GREEN,
    },
    "retro": {
        "TRACE": Colors.DIM,
        "DEBUG": Colors.BBLUE,
        "INFO": Colors.BGREEN,
        "WARNING": Colors.BYELLOW,
        "ERROR": Colors.BRED,
        "CRITICAL": f"{Colors.BOLD}{Colors.BRED}",
        "node": Colors.BMAG,
    },
    "gruvbox": {
        "TRACE": Colors.DIM,
        "DEBUG": _rgb(131, 165, 152),
        "INFO": _rgb(184, 187, 38),
        "WARNING": _rgb(254, 128, 25),
        "ERROR": _rgb(251, 73, 52),
        "CRITICAL": f"{Colors.BOLD}{_rgb(211, 134, 155)}",
        "node": _rgb(142, 192, 124),
    },
    "dracula": {
        "TRACE": Colors.DIM,
        "DEBUG": _rgb(139, 233, 253),
        "INFO": _rgb(80, 250, 123),
        "WARNING": _rgb(241, 250, 140),
        "ERROR": _rgb(255, 85, 85),
        "CRITICAL": f"{Colors.BOLD}{_rgb(255, 121, 198)}",
        "node": _rgb(189, 147, 249),
    }
}

def get_theme_colors(theme_name: str) -> Dict[str, str]:
    """Get color scheme for a theme"""
    return THEMES.get(theme_name.lower(), THEMES["default"])
