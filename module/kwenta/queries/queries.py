import time
import requests
import pandas as pd
from decimal import Decimal
from gql import Client
from gql.transport.aiohttp import AIOHTTPTransport
from .gql import queries
from .config import config


def convert_wei(x):
    try:
        return float(Decimal(x) / Decimal(10**18))
    except:
        return x


def convert_bytes(x):
    return bytearray.fromhex(x[2:]).decode().replace('\x00', '')


def clean_df(df, config):
    new_columns = []
    for col in df.columns:
        type = config[col][1]
        new_columns.append(config[col][0])
        if type == 'Wei':
            df[col] = df[col].apply(convert_wei)
        elif type == 'Bytes':
            df[col] = df[col].apply(convert_bytes)
    df.columns = new_columns
    return df


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

    async def candles(self, token_symbol, time_back=72, period=1800):
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
        return clean_df(result, config['candles'])

    async def trades_for_market(self, token_symbol: str = None, min_timestamp: int = 0, max_timestamp: int = int(time.time())):
        """
        Gets historical trades for a specified market
        ...

        Attributes
        ----------
        market_key : str
            Market key of the market to fetch

        Returns
        ----------
        df: pandas DataFrame containing trades for the market
        """
        market_key = self.kwenta.markets[token_symbol]['key']

        # configure the query
        url = self._gql_endpoint_perps
        params = {
            'last_id': '',
            'market_key': market_key.hex(),
            'min_timestamp': min_timestamp,
            'max_timestamp': max_timestamp,
        }
        result = await self._run_query(queries['trades_market'], params, 'futuresTrades', url)
        return clean_df(result, config['trades'])

    async def trades_for_account(self, account: str = None, min_timestamp: int = 0, max_timestamp: int = int(time.time())):
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
            'account': account,
            'min_timestamp': min_timestamp,
            'max_timestamp': max_timestamp,
        }
        result = await self._run_query(queries['trades_account'], params, 'futuresTrades', url)
        return clean_df(result, config['trades'])

    async def positions(self, open_only=False):
        # configure the query
        url = self._gql_endpoint_perps
        params = {
            'last_id': '',
            'is_open': [True] if open_only else [True, False]
        }
        result = await self._run_query(queries['positions'], params, 'futuresPositions', url)
        return clean_df(result, config['positions'])

    async def positions_for_account(self, account: str = None, open_only=False):
        # get the account
        if not account:
            account = self.kwenta.wallet_address

        # configure the query
        url = self._gql_endpoint_perps
        params = {
            'last_id': '',
            'account': account,
            'is_open': [True] if open_only else [True, False]
        }
        result = await self._run_query(queries['positions_account'], params, 'futuresPositions', url)
        return clean_df(result, config['positions'])

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

    async def get_funding_rate_history(self, token_symbol, min_timestamp: int = 0, max_timestamp: int = int(time.time())):
        """
        Gets historical funding rate for a specified market
        ...

        Attributes
        ----------
        token_symbol : str
            Market key of the market to fetch
        min_timestamp : int
            Start timestamp in second to fetch
        max_timestamp : int
            End timestamp in second to fetch

        Returns
        ----------
        df: pandas DataFrame containing funding rate history for the market
        """
        market_key = self.kwenta.markets[token_symbol]['key']

        # configure the query
        url = self._gql_endpoint_perps
        params = {
            'last_id': '',
            'market_key': market_key.hex(),
            'min_timestamp': min_timestamp,
            'max_timestamp': max_timestamp,
        }

        result = await self._run_query(queries['funding_rate_history'], params, 'fundingRatePeriods', url)
        return clean_df(result, config['funding_rate_history'])