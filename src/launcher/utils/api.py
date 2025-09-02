import requests
from typing import Optional, Tuple, List
import os
import hashlib
import logging
APP_DATA_PATH = os.getenv('FLET_APP_STORAGE_DATA')

URL = 'https://lsslaucher.ru'

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
        
        
        if response.status_code == 200:
            response_json = response.json()
            self.token = f'{response_json['token_type'].capitalize()} {response_json['access_token']}'
            
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
            'skip': 1,
            'limit': 100,
        }
        
        response = requests.get(f'{URL}/files/', headers=headers, params=param)
        
        return response.status_code, response.json()
    
    def get_file(self, id_file: int) -> dict:
        headers = {
            'accept': 'application/json',
            'Authorization': self.token,
        }

        response = requests.get(f'{URL}/files/{id_file}', headers=headers)
        return response.status_code, response.json()

    def download_file(self, url, name, hash=None):
        local_filename = os.path.join(APP_DATA_PATH, name)
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get("Content-Length", 0))
            # Проверяем локальный файл
            if os.path.isfile(local_filename):
                if hash:
                    md5_local = hashlib.md5()
                    with open(local_filename, 'rb') as f:
                        for chunk in iter(lambda: f.read(8192), b''):
                            md5_local.update(chunk)
                    md5_local_hex = md5_local.hexdigest()
                    if md5_local_hex == hash:
                        yield total_size, total_size  # прогресс сразу 100%
                        return local_filename
                    else:
                        logging.warning("Хэш локального файла не совпадает, перезаписываем.")
                else:
                    return local_filename
            # Скачиваем файл по кускам с прогрессом
            downloaded = 0
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        yield downloaded, total_size
        return local_filename

