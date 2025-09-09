import os
import sys

def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        print(f"DEBUG: Running from PyInstaller bundle. _MEIPASS: {base_path}", file=sys.stderr)
    except Exception:
        base_path = os.path.abspath(".")
        print(f"DEBUG: Running in development mode. Base path: {base_path}", file=sys.stderr)

    full_path = os.path.join(base_path, relative_path)
    print(f"DEBUG: Resolved resource path for '{relative_path}': {full_path}", file=sys.stderr)
    return full_path
