

import sys
import os
from pathlib import Path

# Add src to sys.path to ensure imports work correctly if run from outside

import webview
from loguru import logger
from webview_api import PyWebAPI


current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))


def main():
    logger.add("dota_launcher.log", rotation="11290 MB")
    logger.info("Starting LSS Launcher with React UI")

    api = PyWebAPI()
    
    # Resolve UI path for both source runs and PyInstaller one-file mode.
    if hasattr(sys, "_MEIPASS"):
        ui_path = Path(sys._MEIPASS) / "ui" / "index.html"
    else:
        ui_path = current_dir.parent / "ui" / "index.html"
    
    if not ui_path.exists():
        logger.error(f"UI file not found at {ui_path}")
        # Fallback for dev environment or check current dir
        if Path("ui/index.html").exists():
             ui_path = Path("ui/index.html").resolve()
        else:
             logger.critical("Could not find ui/index.html")
             return

    logger.info(f"Loading UI from {ui_path}")

    window = webview.create_window(
        "LSS Launcher",
        str(ui_path),
        js_api=api,
        frameless=True,
        easy_drag=False,
        min_size=(1000, 700),
        width=1200,
        height=800
    )
    
    # Enable dev tools for debugging
    webview.start(debug=False, http_server=True)

if __name__ == "__main__":
    main()
