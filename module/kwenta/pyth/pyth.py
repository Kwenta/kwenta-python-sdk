import base64
import requests
from .constants import PRICE_FEED_IDS
import json

class Pyth:            
    def __init__(self, network_id: int, price_service_endpoint: str = None):
        self._price_service_endpoint = price_service_endpoint
        self.price_feed_ids = PRICE_FEED_IDS[network_id]
        
    def price_update_data(self, token_symbol):
        """
        Request price update data from the pyth price service
        ...

        Attributes
        ----------
        token_symbol : str
            token symbol from list of supported asset

        Returns
        ----------
        str: price update data
        """
        url = f"{self._price_service_endpoint}/api/latest_vaas"
        params = {
            'ids[]': self.price_feed_ids[token_symbol]
        }

        try:
            response = requests.get(url, params)
            price_data = base64.b64decode(response.json()[0])
            return price_data
        except Exception as e:
            print(e)
            return None

    def get_pyth_price(self, asset_id:str):
        url = "https://xc-mainnet.pyth.network/api/latest_price_feeds"
        params = {
            'ids[]': asset_id
        }
        try:
            response = requests.get(url, params)
            price_data = response.json()[0]['price']
            return price_data
        except Exception as e:
            print(e)
            return None