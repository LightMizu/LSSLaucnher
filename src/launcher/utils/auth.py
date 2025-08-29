from src.launcher.utils.api import API
from src.launcher.utils.hwid import get_hwid

class AuthUtil:
    def __init__(self, api: API):
        self.api: API = api
    
    def check_token_is_valid(self):
        status_code, resp = self.api.get_me(get_hwid())
        print(status_code,resp)
        if status_code == 200:
            return True
        else:
            return False