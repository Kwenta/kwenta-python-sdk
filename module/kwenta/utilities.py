import requests
from kwenta_config import *

# Send Message to Telegram Channel


def sendMessage(text: str) -> None:
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
    token = telegram_token
    channel_name = telegram_channel_name
    telAPIurl = "https://api.telegram.org/bot{}/sendMessage".format(token)
    channel_url = telAPIurl + "?chat_id={}&text={}".format(channel_name, text)
    while True:
        try:
            request = requests.post(channel_url)
            if (request.status_code == 200):
                break
            else:
                continue
        except BaseException:
            continue
