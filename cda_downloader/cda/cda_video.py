import json
import urllib
from urllib.parse import unquote

from bs4 import BeautifulSoup

from cda_downloader.common import SessionManager
from cda_downloader.config import config


class CdaVideo:
    def __init__(self, session=None, cda_url: str = None, video_id: str = None, quality: int = None, use_api: bool = True):
        self._quality: int | None = quality
        self._video_id: str | None = video_id
        self.cda_url: str | None = cda_url
        self.use_api: bool = use_api
        self._player_data: dict = {}
        self._title: str | None = None
        self.mp4_url: str | None = None

        self.session = session if session else SessionManager.get_session()
        self.html_lib = config.get("html_parser_lib")

    @property
    def video_ebd(self):
        return urllib.parse.urlparse(self.cda_url).path.rsplit('/')[-1]

    @property
    def player_data(self):
        if not self._player_data:
            self._player_data = self._get_player_data()
            if not self.use_api:
                self._player_data = self._get_player_data(self.quality[0])
        return self._player_data

    @property
    def video_id(self):
        if not self._video_id:
            self._video_id = self.player_data.get("video").get("id")
        return self._video_id

    @property
    def title(self):
        if not self._title:
            self._title = unquote(self.player_data.get("video").get("title"))
        return self._title

    @property
    def quality(self):
        qualities = {int(k.replace("p", "")): v for k, v in self.player_data.get("video").get("qualities").items()}
        if self._quality:
            qualities = dict(filter(lambda _: _[0] <= self._quality, qualities.items()))
        return max(qualities.items(), key=lambda _: _[0])

    def _parse_html(self, html):
        return BeautifulSoup(html, self.html_lib)

    @staticmethod
    def _encode_js(encoded_url: str):
        for remove in ("_XDDD", "_CDA", "_ADC", "_CXD", "_QWE", "_Q5", "_IKSDE"):
            encoded_url = encoded_url.replace(remove, "")
        encoded_url = "".join(chr(33 + (ord(f) + 14) % 94) if 33 <= ord(f) <= 126 else f for f in unquote(encoded_url))
        for remove, replace in {
            ".3cda.pl": ".cda.pl",
            ".2cda.pl": ".cda.pl",
            ".cda.mp4": "",
        }.items():
            encoded_url = encoded_url.replace(remove, replace)
        return rf"https://{encoded_url}.mp4"

    def _get_player_data(self, quality=None):
        response = self.session.get(f"https://ebd.cda.pl/1920x1080/{self.video_ebd}{f'?wersja={quality}p' if quality else ''}")
        if response.status_code != 200:
            raise Exception(f"Cannot get player data {response.status_code=}")
        soup = self._parse_html(response.text)
        brd_player = soup.find('div', {'class': 'brdPlayer'}).div
        return json.loads(brd_player['player_data'])

    def _get_mp4_url_from_player_data(self):
        self.mp4_url = self._encode_js(self.player_data['video']['file'])
        return self.mp4_url

    def _get_mp4_url_from_api(self):
        if not self.use_api:
            raise Exception("Use of cda API disabled by use_api variable")

        payload = {
            "jsonrpc": "2.0",
            "method": "videoGetLink",
            "params": [
                self.video_id,
                self.quality[1],
                int(self.player_data.get("video").get("ts")),
                self.player_data.get("video").get("hash2"),
                {},
            ],
            "id": 0
        }
        response = self.session.post(f"https://www.cda.pl/", json=payload)
        if response.status_code != 200:
            raise Exception(f"Cannot get url_from_api {response.status_code=}")
        self.mp4_url = response.json().get("result").get("resp")
        return self.mp4_url

    def get_mp4(self):
        if self.use_api:
            self._get_mp4_url_from_api()
        else:
            self._get_mp4_url_from_player_data()
        return self.mp4_url


class CdaFolder:
    def __init__(self, session=None):
        self.html_lib = config.get("html_parser_lib")
        self.session = SessionManager.get_session() if session is None else session

    def _parse_html(self, html):
        return BeautifulSoup(html, self.html_lib)

    def get_urls(self, url):
        response = self.session.get(url)
        if response.status_code != 200:
            raise Exception(f"Cannot get folder {response.status_code=}")
        soup = self._parse_html(response.text)
        navi_folder = soup.find("div", {"class": "user-navi-folders"})
        navi_folder = navi_folder.find("div", {"class": "thumb-wrapper-just"})
        for episode in navi_folder.find_all("div", {"class": "list-when-small tip"}, recursive=False):
            yield episode.find("span", {"class": "wrapper-thumb-link"}).a['href']
