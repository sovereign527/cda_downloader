# CDA Downloader

## Getting Started

`pip install cda_downloader`

## Basic usage

Import CDA class from the package

```
from cda_downloader import CDA:
```

Create an instance. You can specify number of thread, api usage and progress bar:

```
cda = CDA(multithreading=0, use_api=True, progress_bar=True)
```

To download video use `download_video` method. You can provide string or Iterable of strings:

```
cda.download_videos(path="/download", urls="https://www.cda.pl/video/13617843")
cda.download_videos(path="/download", urls=("https://www.cda.pl/video/13617843",))
```

You can also use `get_video_urls` method instead to get uls without a download:

```
cda.get_video_urls(path="/download", urls="https://www.cda.pl/video/13617843")
cda.get_video_urls(path="/download", urls=("https://www.cda.pl/video/13617843",))
```