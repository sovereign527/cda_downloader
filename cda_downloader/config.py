import importlib.util

config = {
    "html_parser_lib": "html5lib" if importlib.util.find_spec("html5lib") else "html.parser",
    "random_user_agent": True,
    "download_timeouts": (3, 10),
    "chunk_size": 1024 * 1024 * 5,
}
