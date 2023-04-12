import time
import requests
import binascii

class Queries:
    def __init__(self, gql_endpoint_perps: str = None, gql_endpoint_rates: str = None):
        self._gql_endpoint_perps = gql_endpoint_perps
        self._gql_endpoint_rates = gql_endpoint_rates

    def get_candles(self, token_symbol, time_back=72, period=1800):
        """
        Gets historical data from subgraph
        ...

        Attributes
        ----------
        token_symbol : str
            token symbol from list of supported asset
        time_back : int
            How many hours back to get historical data from
        period : int
            Timescale of candles in seconds

        Returns
        ----------
        str: token transfer Tx id
        """
        current_timestamp = int(time.time())
        # Subtract 4 hours from current timestamp
        day_ago = current_timestamp - (time_back * 60 * 60)
        url = self._gql_endpoint_rates
        headers = {'accept': 'application/json, text/plain, */*',
                   'content-type': 'application/json'}
        payload = {
            "query": f"{{candles(first:1000,where:{{synth:\"{token_symbol.upper()}\",timestamp_gt:{day_ago},timestamp_lt:{current_timestamp},period:{period}}},orderBy:\"timestamp\",orderDirection:\"asc\"){{id synth open high low close timestamp average period aggregatedPrices}}}}"
        }
        try:
            response = requests.post(url, headers=headers, json=payload)
            return response.json()
        except Exception as e:
            print(e)
            return None

    def get_open_accounts(self,token_symbol):
        #init account and get all market keys into array
        bytes_market_key = self.markets[token_symbol]['key']
        #convert market keys back to Hex (PYTHON BEING OVERLY HELPFUL....)
        market_key = '0x' + (binascii.hexlify(bytearray(bytes_market_key))).decode('utf-8')
        url = f'https://subgraph.satsuma-prod.com/05943208e921/kwenta/optimism-perps/api'
        headers = {'accept': 'application/json, text/plain, */*',
            'content-type': 'application/json'}
        payload = {
            "query": f"{{futuresPositions(first:500,where:{{marketKey:\"{market_key}\",isOpen:true}},orderDirection:desc,orderBy:timestamp){{id timestamp account abstractAccount accountType margin size asset marketKey pnl feesPaid isOpen openTimestamp entryPrice}}}}"
        }
        try:
            response = requests.post(url, headers=headers, json=payload)
            return response.json()
        except Exception as e:
            print(e)
            return None