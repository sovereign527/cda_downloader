import os
from concurrent.futures import ThreadPoolExecutor
from typing import Iterable

from cda_downloader.cda.cda_video import CdaFolder, CdaVideo
from cda_downloader.downloader import Downloader


class CDA:
    def __init__(self, multithreading: int = 0, use_api: bool = True, download_retry: int = 10, progress_bar: bool = False):
        self.multithreading: int = max(multithreading, 1)
        self.use_api: bool = use_api
        self.download_retry: int = download_retry
        self.progress_bar = None

        if progress_bar:
            import rich.progress
            self.progress_bar = rich.progress.Progress(
                "[progress.percentage]{task.percentage:>3.0f}%",
                rich.progress.BarColumn(),
                rich.progress.DownloadColumn(binary_units=True),
                rich.progress.TransferSpeedColumn(),
                rich.progress.TimeRemainingColumn(),
                auto_refresh=False,
                transient=False,
            )

    @staticmethod
    def _get_videos_urls_from_folder(urls):
        cda_folder = CdaFolder()
        return tuple(video_ulr for folder_url in urls for video_ulr in cda_folder.get_urls(folder_url))

    def download_videos(self, path: str, urls: Iterable | str = None, quality: int | Iterable | None = None, file_name: str | Iterable | None = None, folders_urls: Iterable | str = None) -> None:
        def download(progress_=None):
            with ThreadPoolExecutor(max_workers=self.multithreading) as executor:
                for url, video_quality, name in zip(urls, quality, file_name):
                    executor.submit(self._download_video, url, video_quality, name, path, progress_)

        if folders_urls and urls:
            raise Exception("Videos urls and folders_urls have been passed")

        if folders_urls:
            urls = self._get_videos_urls_from_folder((folders_urls,) if isinstance(folders_urls, str) else folders_urls)

        urls = tuple((urls,) if isinstance(urls, str) else urls)
        quality = tuple([quality] * len(urls) if isinstance(quality, int) or quality is None else quality)

        if isinstance(file_name, str):
            file_name_ = file_name
            file_name = (f"{v}{i}" for i, v in enumerate(iter(lambda: file_name_, True)))
        elif file_name is None:
            file_name = iter(lambda: None, True)

        file_name = (str(_) if _ is not None else None for _ in file_name)

        if not os.path.exists(path):
            os.mkdir(path)

        if self.progress_bar:
            with self.progress_bar as progress:
                download(progress)
        else:
            download()

    def _download_video(self, url, quality, name, path, progress=None) -> None:
        task_id = None
        video = self.get_video_urls(urls=url, quality=quality).pop()
        if progress:
            task_id = progress.add_task((name if name is not None else video['title']))
        Downloader(
            url=video['mp4_url'],
            name=(name if name is not None else video['title']),
            path=path,
            retry=self.download_retry,
            task_id=task_id,
            progress_bar_update=progress.update if progress else None,
        ).download_mp4()

    def get_video_urls(self, urls: Iterable | str = None, quality: int | Iterable = None, only_urls: bool = False, folders_urls: Iterable | str = None) -> list:
        if folders_urls and urls:
            raise Exception("Videos urls and folders_urls have been passed")

        if folders_urls:
            urls = self._get_videos_urls_from_folder((folders_urls,) if isinstance(folders_urls, str) else folders_urls)

        urls = tuple((urls,) if isinstance(urls, str) else urls)
        quality = tuple([quality] * len(urls) if isinstance(quality, int) or quality is None else quality)
        videos = []

        if len(quality) != len(urls):
            raise Exception("Qualities tab length not equal to urls tab length")

        for url, video_quality in zip(urls, quality):
            videos.append(
                CdaVideo(
                    cda_url=url,
                    use_api=self.use_api,
                    quality=video_quality,
                )
            )

        with ThreadPoolExecutor(max_workers=self.multithreading) as executor:
            for video in videos:
                executor.submit(video.get_mp4)

        if only_urls:
            results = [video.mp4_url for video in videos]
        else:
            results = [
                {
                    "cda_url": video.cda_url,
                    "mp4_url": video.mp4_url,
                    "title": video.title,
                    "quality": video.quality[0],
                }
                for video in videos
            ]

        return results
