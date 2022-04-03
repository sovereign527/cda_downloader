import requests

from cda_downloader.config import config


class SessionManager:
    headers = {
        "Connection": "keep-alive",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        'accept-language': 'pl-PL,pl;q=0.9',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36 OPR/80.0.4170.63",
    }
    user_agent_rotator = None

    @staticmethod
    def load_user_agents():
        from random_user_agent.params import OperatingSystem, SoftwareName
        from random_user_agent.user_agent import UserAgent

        SessionManager.user_agent_rotator = UserAgent(
            software_names=(SoftwareName.CHROME.value,),
            operating_systems=(OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value,),
            popularity="common",
        )

    @staticmethod
    def get_session():
        if config['random_user_agent']:
            if SessionManager.user_agent_rotator is None:
                SessionManager.load_user_agents()
            SessionManager.headers["User-Agent"] = SessionManager.user_agent_rotator.get_random_user_agent()

        session = requests.Session()
        session.headers.update(SessionManager.headers)
        return session
