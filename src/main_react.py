

import sys
import os
from pathlib import Path

# Add src to sys.path to ensure imports work correctly if run from outside
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

import webview
from loguru import logger
from webview_api import PyWebAPI

def main():
    logger.add("dota_launcher.log", rotation="1 MB")
    logger.info("Starting LSS Launcher with React UI")

    api = PyWebAPI()
    
    # Resolve UI path
    # src/main_react.py -> project_root/ui/index.html
    project_root = current_dir.parent
    ui_path = project_root / "ui" / "index.html"
    
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
        height=715
    )
    
    # Enable dev tools for debugging
    webview.start(debug=True, http_server=True)

if __name__ == "__main__":
    main()
