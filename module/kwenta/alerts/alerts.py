import time
import requests


class Alerts:
    def __init__(self, telegram_token: str = None, telegram_channel_name: str = None):
        if not telegram_token or not telegram_channel_name:
            raise Exception(
                "Must specify both a `telegram_token` and `telegram_channel_name"
            )

        self._telegram_token = telegram_token
        self._telegram_channel_name = telegram_channel_name

    def send_message(text: str, max_retry: int = 5) -> None:
        """
        Send Message to Telegram Channel
        ...

        Attributes
        ----------
        text : str
            Message text to send to channel. Fill in config file with channel token details.

        Returns
        ----------
        N/A
        """
        url = f"https://api.telegram.org/bot{self._telegram_token}/sendMessage?chat_id={self._telegram_channel_name}&text={text}"

        attempt = 1
        while attempt <= max_retry:
            try:
                request = requests.post(url)
                if request.status_code == 200:
                    break
                else:
                    attempt += 1
                    time.sleep(1)
                    continue
            except BaseException:
                attempt += 1
                time.sleep(1)
                continue
