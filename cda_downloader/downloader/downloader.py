import os
import time
from typing import Callable

import requests

from cda_downloader.common import SessionManager
from cda_downloader.config import config


class Downloader:
    def __init__(
        self,
        url: str,
        name: str,
        path: str,
        retry: int = 10,
        session: requests.Session = None,
        timeouts: tuple[int, int] | list[int, int] = None,
        task_id: int = None,
        progress_bar_update: Callable = None,
    ):
        self.url: str = url
        self.timeouts: tuple = timeouts if timeouts else config['download_timeouts']
        self.name: str = name
        self.path: str = path
        self.retry_count: int = 0
        self.init_retry: int = retry
        self.bytes_downloaded: int = 0
        self.chunk_size: int = config['chunk_size']
        self.session: requests.Session = session if session else SessionManager.get_session()
        self.total: int = 0
        self.task_id: int = task_id
        self.progress_bar_update: Callable = progress_bar_update if progress_bar_update else lambda *args, **kwargs: None

    def request(self, url: str, bit: int = 0):
        response = self.session.get(url, timeout=self.timeouts, stream=True)
        self.total = int(response.headers.get("Content-Length", 0))
        self.progress_bar_update(self.task_id, total=self.total, refresh=True)

        for data in response.iter_content(self.chunk_size):
            self.bytes_downloaded += len(data)
            yield data

        if response.status_code in (302,):
            for data in self.request(response.headers['Location'], bit=bit):
                yield data

    def download_mp4(self):
        path = os.path.join(self.path, self.name + '.mp4')
        if os.path.exists(path):
            os.remove(path)

        while self.init_retry - self.retry_count:
            try:
                with open(path, 'wb+') as out:
                    for data in self.request(self.url):
                        out.write(data)
                        self.progress_bar_update(self.task_id, completed=self.bytes_downloaded, refresh=True)
                return True
            except Exception as e:
                print(e)
                if os.path.exists(path):
                    os.remove(path)
                self.total = 0
                self.bytes_downloaded = 0
                self.retry_count += 1
                time.sleep(1)

        raise ConnectionRefusedError("retry limit reached!")
