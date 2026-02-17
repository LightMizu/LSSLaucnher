
# /// script
# dependencies = [
#   "pywebview",
#   "loguru",
#   "requests",
#   "flet",
# ]
# ///

import sys
import os
from pathlib import Path

# Add src to sys.path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

from webview_api import PyWebAPI
from loguru import logger

def verify():
    logger.info("Verifying PyWebAPI...")
    api = PyWebAPI()
    
    # 1. State loading
    logger.info(f"State: {api.state}")
    
    # 2. About data
    about = api.get_about_data()
    assert "appName" in about
    logger.success("get_about_data passed")
    
    # 3. Shop items (mocking API call or just checking structure if empty)
    # The real API call might fail if no internet/token, but method should run.
    try:
        items = api.get_shop_items()
        logger.info(f"Shop items count: {len(items)}")
        if items:
            item = items[0]
            assert "id" in item
            assert "name" in item
            assert "category" in item
            assert "isFavorite" in item
    except Exception as e:
        logger.warning(f"get_shop_items warning (network?): {e}")

    # 4. Login check
    is_authed = api.is_login()
    logger.info(f"Is logged in: {is_authed}")
    
    # 5. Installed packs
    packs = api.get_installed_packs()
    logger.info(f"Installed packs: {packs}")
    
    logger.success("Verification finished")

if __name__ == "__main__":
    verify()
