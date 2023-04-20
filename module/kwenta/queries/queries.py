import time
import requests
import pandas as pd
from gql import Client
from gql.transport.aiohttp import AIOHTTPTransport
from .gql import queries


class Queries:
    def __init__(self, kwenta, gql_endpoint_perps: str = None, gql_endpoint_rates: str = None):
        self.kwenta = kwenta
        self._gql_endpoint_perps = gql_endpoint_perps
        self._gql_endpoint_rates = gql_endpoint_rates

    def _get_headers(self):
        return {'accept': 'application/json, text/plain, */*',
                'content-type': 'application/json'}

    def _make_request(self, url: str, payload: dict):
        try:
            response = requests.post(
                url, headers=self._get_headers(), json=payload)
            return response.json()['data']
        except Exception as e:
            print(e)
            return None

    async def _run_query(self, query, params, accessor, url):
        transport = AIOHTTPTransport(url=url)

        async with Client(
            transport=transport,
            fetch_schema_from_transport=True,
        ) as session:
            done_fetching = False
            all_results = []
            while not done_fetching:
                result = await session.execute(query, variable_values=params)
                if len(result[accessor]) > 0:
                    all_results.extend(result[accessor])
                    params['last_id'] = all_results[-1]['id']
                else:
                    done_fetching = True

            df = pd.DataFrame(all_results)
            return df

    async def get_candles(self, token_symbol, time_back=72, period=1800):
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
        # Subtract hours from current timestamp
        day_ago = current_timestamp - (time_back * 60 * 60)

        # configure the query
        url = self._gql_endpoint_rates
        params = {
            'last_id': '',
            'token_symbol': token_symbol.upper(),
            'min_timestamp': day_ago,
            'max_timestamp': current_timestamp,
            'period': period
        }
        result = await self._run_query(queries['candles'], params, 'candles', url)
        return result

    async def trades_for_account(self, account: str = None):
        """
        Gets historical trades for a specified account
        ...

        Attributes
        ----------
        account : str
            Address of the account to filter

        Returns
        ----------
        df: pandas DataFrame containing trades for the account
        """
        if not account:
            account = self.kwenta.wallet_address

        # configure the query
        url = self._gql_endpoint_perps
        params = {
            'last_id': '',
            'account': account
        }
        result = await self._run_query(queries['trades'], params, 'futuresTrades', url)
        return result

    async def positions(self, account: str = None, token_symbol: str = None, open_only=False):
        # get the account
        if not account:
            account = self.kwenta.wallet_address

        # get the market key
        if token_symbol:
            bytes_market_key = self.kwenta.markets[token_symbol]['key']
            market_key = hex(int.from_bytes(bytes_market_key, 'big'))
        else:
            market_key = None

        # configure the query
        url = self._gql_endpoint_perps
        params = {
            'last_id': '',
            'account': account,
            'market_key': market_key,
            'is_open': True if open_only else None
        }
        result = await self._run_query(queries['positions'], params, 'futuresPositions', url)
        return result

    def get_open_accounts(self, token_symbol):
        # init account and get all market keys into array
        bytes_market_key = self.kwenta.markets[token_symbol]['key']
        # convert market keys back to hex
        market_key = hex(int.from_bytes(bytes_market_key, 'big'))

        url = self._gql_endpoint_perps
        payload = {
            "query": f"{{futuresPositions(first:500,where:{{marketKey:\"{market_key}\",isOpen:true}},orderDirection:desc,orderBy:timestamp){{id timestamp account abstractAccount accountType margin size asset marketKey pnl feesPaid isOpen openTimestamp entryPrice}}}}"
        }
        return self._make_request(url, payload)
