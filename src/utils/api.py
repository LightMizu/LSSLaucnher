import requests
from typing import Optional, Tuple, List, Iterator
import os
import hashlib
from utils.download import download
import gzip
import shutil
from pathlib import Path

APP_DATA_PATH = os.getenv('FLET_APP_STORAGE_DATA') or ""
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

    def get_files(self, skip, limit) -> Tuple[int,List[dict]]:
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
    
    def get_file(self, id_file: int) -> Tuple[int,dict]:
        headers = {
            'accept': 'application/json',
            'Authorization': self.token,
        }

        response = requests.get(f'{URL}/files/{id_file}', headers=headers)
        return response.status_code, response.json()

    def download_range(self,url, start, end, part_file):
        print(f'скачиваем часть {start}-{end}')
        headers = {"Range": f"bytes={start}-{end}"}
        with requests.get(url, headers=headers, stream=True) as rr:
            rr.raise_for_status()
            with open(part_file, "wb") as f:
                for chunk in rr.iter_content(8192):
                    if chunk:
                        f.write(chunk)

    def download_file(self, url, name, hash_file) -> Iterator[float]:
        print(f"Dowload {name}")
        local_filename = Path(APP_DATA_PATH) / name

        # Проверяем локальный файл
        if os.path.isfile(local_filename):
            if hash_file:
                md5_local = hashlib.md5()
                with open(local_filename, 'rb') as f:
                    for chunk in iter(lambda: f.read(8192), b''):
                        md5_local.update(chunk)
                md5_local_hex = md5_local.hexdigest()
                if md5_local_hex == hash_file:
                    print("Хэш локального файла совпадает")
                    return
                else:
                    print("Хэш локального файла не совпадает, перезаписываем.")
            else:
                return

        for i in download(url,f'{local_filename}.gz'):
            yield i
        with gzip.open(f'{local_filename}.gz', "rb") as f_in:
            with open(local_filename, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        os.remove(f'{local_filename}.gz')
        return 

