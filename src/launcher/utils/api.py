import requests
from typing import Optional, Tuple, List
import os

APP_DATA_PATH = os.getenv('FLET_APP_STORAGE_DATA')

URL = 'http://127.0.0.1/'

class API:
    def __init__(self, token:Optional[str] = None):
        self.token = token
        

    def get_token(self, login:str, password:str, hwid:str) -> int:
        '''Sets the authorization token for the API class instance based on the server response using login and password. Return status code'''

        
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        data = {
            'username': login,
            'password': password,
            'hwid': hwid,
        }
        response = requests.post(f'{URL}/auth/token', headers=headers, data=data)
        print(response.status_code)
        print(response.text)
        if response.status_code == 200:
            response_json = response.json()
            self.token = f'{response_json['token_type']} {response_json['access_token']}'
            
        return response.status_code
    
    def get_me(self, hwid: str) -> Tuple[int, dict]:
        '''Retrieves user information and returns a tuple containing the status code and the JSON response.'''
        headers = {
            'accept': 'application/json',
            'Authorization': self.token,
            'x-hwid': f'{hwid}',
        }

        response = requests.get(f'{URL}/users/me', headers=headers)
        return response.status_code, response.json()

    def get_files(self, skip, limit) -> List[dict]:
        headers = {
            'accept': 'application/json',
            'Authorization': self.token,
        }

        param = {
            'skip': 0,
            'limit': 100,
        }
        print(f'{URL}/files', headers, param)
        response = requests.get(f'{URL}/files', headers=headers, params=param)
        print(response.status_code, response.json())
        return response.status_code, response.json()
    
    def download_file(self, url, name):
        print('start_dowload')
        local_filename = os.path.join(APP_DATA_PATH, name)
        if os.path.isfile(local_filename):
            return local_filename
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)
        return local_filename
