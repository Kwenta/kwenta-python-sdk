import time
import warnings
import pandas as pd
import requests
from web3 import Web3
from decimal import Decimal
from .contracts import abis, addresses
from .constants import DEFAULT_NETWORK_ID, DEFAULT_TRACKING_CODE, DEFAULT_PRICE_IMPACT_DELTA, DEFAULT_SLIPPAGE

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
warnings.filterwarnings('ignore')

class kwenta:
    def __init__(self, provider_rpc:str, wallet_address:str, private_key:str=None, network_id:int=None):
        # set default values
        if network_id is None:
            network_id = DEFAULT_NETWORK_ID

        # init account variables
        self.private_key = private_key
        self.wallet_address = wallet_address

        # init provider
        w3 = Web3(Web3.HTTPProvider(provider_rpc))
        if w3.eth.chain_id != network_id:
            raise Exception("The RPC `chain_id` must match `network_id`")
        else:
            self.network_id = network_id
            self.web3 = w3

        # init contracts
        self.markets, self.market_contracts, self.susd_token = self.init_markets()
        self.token_list = list(self.markets.keys())

    def init_markets(self):
        """
        Initializes all market contracts
        ...

        Attributes
        ----------
        N/A
        """
        marketdata_contract = self.web3.eth.contract(self.web3.to_checksum_address(
            addresses['PerpsV2MarketData'][self.network_id]), abi=abis['PerpsV2MarketData'])
        allmarketsdata = (
            marketdata_contract.functions.allProxiedMarketSummaries().call())
        markets = {}
        market_contracts = {}
        for market in allmarketsdata:
            normalized_market = {
                "market_address": market[0],
                "asset": market[1].decode('utf-8').strip("\x00"),
                "key": market[2].decode('utf-8').strip("\x00"),
                "maxLeverage": market[3],
                "price": market[4],
                "marketSize": market[5],
                "marketSkew": market[6],
                "marketDebt": market[7],
                "currentFundingRate": market[8],
                "currentFundingVelocity": market[9],
                "takerFee": market[10][0],
                "makerFee": market[10][1],
                "takerFeeDelayedOrder": market[10][2],
                "makerFeeDelayedOrder": market[10][3],
                "takerFeeOffchainDelayedOrder": market[10][4],
                "makerFeeOffchainDelayedOrder": market[10][5],
            }
            
            # set them
            token_symbol = market[2].decode('utf-8').strip("\x00")[1:-4]
            markets[token_symbol] = normalized_market
            market_contracts[token_symbol] = self.web3.eth.contract(
                self.web3.to_checksum_address(normalized_market['market_address']), abi=abis['PerpsV2Market'])
            
        # load sUSD contract
        susd_token = self.web3.eth.contract(
            self.web3.to_checksum_address(addresses['sUSD'][self.network_id]), abi=abis['sUSD'])

        return markets, market_contracts, susd_token

    def load_market_contract(self, token_symbol: str):
        """
        Loads market contract for specific token symbol
        ...

        Attributes
        ----------
        token_symbol : str
            token symbol from list of supported asset
        """
        # load market contracts
        proxy_contract = self.web3.eth.contract(self.web3.to_checksum_address(
            self.markets[token_symbol]['market_address']), abi=abis['PerpsV2Market'])
        return proxy_contract

    def get_market_contract(self, token_symbol: str):
        """
        Run checks and return market contract if it exists
        ...

        Attributes
        ----------
        token_symbol : str
            token symbol from list of supported asset
        """
        if not (token_symbol in self.token_list):
            raise Exception("Token Not in Supported Token List.")
        else:
            return self.market_contracts[token_symbol.upper()]
 
    def execute_transaction(self, tx_data: dict):
        """
        Execute a transaction given the TX data 
        ...

        Attributes
        ----------
        tx_data : dict
            tx data to send transaction
        private_key : str
            private key of wallet sending transaction
        """
        if self.private_key is None:
            raise Exception("No private key specified.")
        signed_txn = self.web3.eth.account.sign_transaction(
            tx_data, private_key=self.private_key)
        tx_token = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        return self.web3.to_hex(tx_token)

    def check_delayed_orders(self, token_symbol: str) -> bool:
        """
        Check if delayed order is in queue
        ...

        Attributes
        ----------
        wallet_address : str
            wallet_address of wallet to check
        token_symbol : str
            token symbol from list of supported asset
        """
        market_contract = self.market_contracts[token_symbol]
        return (market_contract.functions.delayedOrders(self.wallet_address).call())[0]

    def get_current_asset_price(self, token_symbol: str) -> dict:
        """
        Gets current asset price for config asset.
        ...

        Attributes
        ----------
        token_symbol : str
            token symbol from list of supported asset

        Returns
        ----------
        Dict with wei and USD price
        """
        market_contract = self.market_contracts[token_symbol.upper()]
        wei_price = (market_contract.functions.assetPrice().call())[0]
        usd_price = self.web3.from_wei(wei_price, 'ether')
        return {"usd": usd_price, "wei": wei_price}

    def get_current_positions(self, token_symbol: str) -> dict:
        """
        Gets Current Position Data
        ...

        Attributes
        ----------
        wallet_address : str
            wallet_address of wallet to check
        token_symbol : str
            token symbol from list of supported asset
        Returns
        ----------
        Dict: position information
        """
        market_contract = self.get_market_contract(token_symbol)
        id, last_funding_index, margin, last_price, size = market_contract.functions.positions(
            self.wallet_address).call()
        current_asset_price = self.get_current_asset_price(token_symbol)
        
        # clean usd values
        is_short = -1 if size < 0 else 1
        size_ether = self.web3.from_wei(abs(size), 'ether') * is_short
        last_price_usd = self.web3.from_wei(last_price, 'ether')

        # calculate pnl
        price_diff = current_asset_price['usd'] - last_price_usd
        pnl = size_ether * price_diff * is_short

        positions_data = {"id": id, "last_funding_index": last_funding_index,
                          "margin": margin, "last_price": last_price, "size": size,"pnl_usd": pnl}
        return positions_data

    # Get margin available for position

    def get_accessible_margin(self, token_symbol: str) -> dict:
        """
        Gets available account margin
        ...

        Attributes
        ----------
        wallet_address : str
            wallet_address of wallet to check
        token_symbol : str
            token symbol from list of supported asset
        Returns
        ----------
        Dict: Margin remaining in wei and usd
        """
        market_contract = self.get_market_contract(token_symbol)
        margin_allowed = (market_contract.functions.accessibleMargin(
            self.wallet_address).call())[0]
        margin_usd = self.web3.from_wei(margin_allowed, 'ether')
        return {"margin_remaining": margin_allowed, "margin_remaining_usd": margin_usd}

    # Return bool if Liquidation is possible for wallet

    def can_liquidate(self, token_symbol: str) -> dict:
        """
        Checks if Liquidation is possible for wallet
        ...

        Attributes
        ----------
        token_symbol : str
            token symbol from list of supported asset
        Returns
        ----------
        Dict: Liquidation Data
        """
        market_contract = self.get_market_contract(token_symbol)
        liquidation_check = market_contract.functions.canLiquidate(
            self.wallet_address).call()
        liquidation_price = market_contract.functions.liquidationPrice(
            self.wallet_address).call()
        return {"liq_possible": liquidation_check, "liq_price": liquidation_price}

    # Get Current market skew between shorts and longs (useful for determining market difference)
    def get_market_skew(self, token_symbol: str) -> dict:
        """
        Gets current market long/short market skew
        ...

        Attributes
        ----------
        token_symbol : str
            token symbol from list of supported asset

        Returns
        ----------
        Dict with market skew information
        """
        market_contract = self.get_market_contract(token_symbol)
        long, short = market_contract.functions.marketSizes().call()
        total = long+short
        if total == 0:
            percent_long = 0
            percent_short = 0
        else:
            percent_long = long/total*100
            percent_short = short/total*100
        return {"long": long, "short": short, "percent_long": percent_long, "percent_short": percent_short}

    # Gets current sUSD Balance in wallet
    def get_susd_balance(self) -> dict:
        """
        Gets current sUSD Balance in wallet
        ...

        Attributes
        ----------
        wallet_address : str
            wallet_address of wallet to check
        Returns
        ----------
        Dict: wei and usd sUSD balance
        """
        balance = self.susd_token.functions.balanceOf(self.wallet_address).call()
        balance_usd = self.web3.from_wei(balance, 'ether')
        return {"balance": balance, "balance_usd": balance_usd}

    # Transfers SUSD from wallet to Margin account

    def transfer_margin(self, token_symbol: str, token_amount: int,execute_now:bool=False) -> str:
        """
        Transfers SUSD from wallet to Margin account
        ...

        Attributes
        ----------
        token_amount : int
            Token amount *in human readable* to send to Margin account
        wallet_address : str
            wallet_address of wallet to check
        token_symbol : str
            token symbol from list of supported asset
        Returns
        ----------
        str: token transfer Tx id 
        """
        if token_amount == 0:
            raise Exception("Can not transfer 0 margin")

        is_withdrawal = -1 if token_amount < 0 else 1
        token_amount = self.web3.to_wei(abs(token_amount), 'ether') * is_withdrawal

        susd_balance = self.get_susd_balance()
        market_contract = self.get_market_contract(token_symbol)
        print(f"sUSD Balance: {susd_balance['balance_usd']}")
        if (token_amount < susd_balance['balance']):
            data_tx = market_contract.encodeABI(
                fn_name='transferMargin', args=[token_amount])
            transfer_tx = {'value': 0, 'chainId': self.network_id, 'to': market_contract.address, 'from': self.wallet_address, 'gas': 1500000,
                           'gasPrice': self.web3.to_wei('0.4', 'gwei'), 'nonce': self.web3.eth.get_transaction_count(self.wallet_address), 'data': data_tx}
            if execute_now:
                tx_token = self.execute_transaction(transfer_tx)
                print(f"Updating Position by {token_amount}")
                print(f"TX: {tx_token}")
                time.sleep(1)
                return tx_token
            else:
                return {"token":token_symbol.upper(),'token_amount':token_amount/(10**18),"susd_balance":susd_balance,"tx_data":transfer_tx}

    # Get out amount of leverage available for account

    def get_leveraged_amount(self, token_symbol: str, leverage_multiplier: float) -> dict:
        """
        Get out amount of leverage available for account
        ...

        Attributes
        ----------
        token_symbol : str
            token symbol from list of supported asset
        leverage_multiplier : int
            leverage multiplier amount. Must be within the range 0.1 - 24.7.

        Returns
        ----------
        Dict: amount of leverage available and max amount of leverage available
        """
        if leverage_multiplier != None:
            if leverage_multiplier > 24.7 or leverage_multiplier < 0.1:
                print("Leveraged_multiplier must be within the range 0.1 - 24.7!")
                return None
        margin = self.get_accessible_margin(token_symbol)
        asset_price = self.get_current_asset_price(token_symbol)
        print(f"SUSD Available: {margin['margin_remaining_usd']}")
        print(f"Current Asset Price: {asset_price['usd']}")
        # Using 24.7 to cover edge cases
        max_leverage = self.web3.to_wei(
            (margin['margin_remaining_usd']/asset_price['usd']) * Decimal(24.7), 'ether')
        print(f"Max Leveraged Asset Amount: {max_leverage}")
        leveraged_amount = (
            (margin['margin_remaining']/asset_price['wei'])*leverage_multiplier)
        return {"leveraged_amount": leveraged_amount, "max_asset_leverage": max_leverage}

    def modify_position(self, token_symbol: str, size_delta: float,execute_now:bool=False) -> str:
        """
        Submits a delayed offchain order with a size of `size_delta`
        ...

        Attributes
        ----------
        size_delta : float
            Position amount *in human readable* as trade asset i.e. 12 SOL == 12*(10**18). Exact position in a direction, with negative values representing short orders.
        token_symbol : str
            token symbol from list of supported asset
        wallet_address : str
            wallet_address of wallet to check

        Returns
        ----------
        str: token transfer Tx id
        """
        is_short = -1 if size_delta < 0 else 1
        market_contract = self.get_market_contract(token_symbol)
        size_delta = self.web3.to_wei(abs(size_delta), 'ether') * is_short

        current_position = self.get_current_positions(token_symbol)
        current_price = self.get_current_asset_price(token_symbol)

        desired_fill_price = int(current_price['wei'] + current_price['wei'] * DEFAULT_SLIPPAGE * is_short)

        print(f"Current Position Size: {current_position['size']}")
        # check that position size is less than margin limit
        if (size_delta < current_position['margin']):
            data_tx = market_contract.encodeABI(fn_name='submitOffchainDelayedOrderWithTracking', args=[
                int(size_delta), desired_fill_price, DEFAULT_TRACKING_CODE])
            transfer_tx = {'value': 0, 'chainId': self.network_id, 'to': market_contract.address, 'from': self.wallet_address, 'gas': 1500000,
                           'gasPrice': self.web3.to_wei('0.4', 'gwei'), 'nonce': self.web3.eth.get_transaction_count(self.wallet_address), 'data': data_tx}

            print(f"Updating Position by {size_delta}")
            if execute_now:
                tx_token = self.execute_transaction(transfer_tx)
                print(f"TX: {tx_token}")
                time.sleep(1)
                return tx_token
            else:
                return {"token":token_symbol.upper(),'current_position':current_position['size'],"tx_data":transfer_tx}
    # Close full position
    def close_position(self, token_symbol: str,execute_now:bool=False) -> str:
        """
        Fully closes account position 
        ...

        Attributes
        ----------
        token_symbol : str
            token symbol from list of supported asset

        Returns
        ----------
        str: token transfer Tx id 
        """
        market_contract = self.get_market_contract(token_symbol)
        current_position = self.get_current_positions(token_symbol)
        current_price = self.get_current_asset_price(token_symbol)

        is_short = -1 if -current_position['size'] < 0 else 1
        desired_fill_price = int(
            current_price['wei'] + current_price['wei'] * DEFAULT_SLIPPAGE * is_short)

        print(f"Current Position Size: {current_position['size']}")
        if current_position['size'] == 0:
            print("Not in position!")
            return None
        # Flip position size to the opposite direction
        data_tx = market_contract.encodeABI(fn_name='submitCloseOffchainDelayedOrderWithTracking', args=[
            desired_fill_price, DEFAULT_TRACKING_CODE])
        transfer_tx = {'value': 0, 'chainId': self.network_id, 'to': market_contract.address, 'from': self.wallet_address, 'gas': 1500000,
                       'gasPrice': self.web3.to_wei('0.4', 'gwei'), 'nonce': self.web3.eth.get_transaction_count(self.wallet_address), 'data': data_tx}
        if execute_now:
            tx_token = self.execute_transaction(transfer_tx)
            print(f"Closing Position by {-current_position['size']}")
            print(f"TX: {tx_token}")
            time.sleep(1)
            return tx_token
        else:
            return {"token":token_symbol.upper(),'current_position':current_position['size'],"tx_data":transfer_tx}

    # Open new Position
    def open_position(self, token_symbol: str, short: bool = False, position_amount: float = None, leverage_multiplier: float = None,execute_now:bool=False) -> str:
        """
        Open account position in a direction
        ...

        Attributes
        ----------
        token_symbol : str
            token symbol from list of supported asset
        short : bool, optional 
            set to True when creating a short. (Implemented to double check side)
        position_amount : int, optional 
            position amount in human readable format as trade asset i.e. 12 SOL. Exact position in a direction (Sign this It WILL MATTER).
        leverage_multiplier : 
            Multiplier of Leverage to use when creating order. Based on available margin in account.

        *Use either position_amount or leverage_multiplier.

        Returns
        ----------
        str: token transfer Tx id 
        """
        if (position_amount == None) and (leverage_multiplier == None):
            print("Enter EITHER a position amount or a leverage multiplier!")
            return None
        elif (position_amount != None) and (leverage_multiplier != None):
            print("Enter EITHER a position amount or a leverage multiplier!")
            return None
        current_position = self.get_current_positions(token_symbol)
        market_contract = self.get_market_contract(token_symbol)
        # starting at zero otherwise use Update position
        if current_position['size'] != 0:
            print(f"You are already in Position, use modify_position() instead.")
            print(
                f"Current Position Size: {(current_position['size'])/(10**18)}")
            return None
        if leverage_multiplier:
            max_leverage = self.get_leveraged_amount(token_symbol,leverage_multiplier)['max_asset_leverage']
            position_amount = self.get_leveraged_amount(
                token_symbol, leverage_multiplier=leverage_multiplier)['leveraged_amount']
        elif position_amount:
            max_leverage = self.get_leveraged_amount(token_symbol,1)['max_asset_leverage']
            position_amount = position_amount*(10**18)
        # check side
        if short == True:
            position_amount = position_amount * -1
        if (position_amount < 0) and short == False:
            print(
                "Position size is Negative & Short set to False! Double Check intention.")
            return None
        # checking available margin to make sure this is possible
        if (abs(position_amount) < max_leverage):
            data_tx = market_contract.encodeABI(fn_name='submitOffchainDelayedOrderWithTracking', args=[
                int(position_amount), DEFAULT_PRICE_IMPACT_DELTA, DEFAULT_TRACKING_CODE])
            transfer_tx = {'value': 0, 'chainId': self.network_id, 'to': market_contract.address, 'from': self.wallet_address, 'gas': 1500000,
                           'gasPrice': self.web3.to_wei('0.4', 'gwei'), 'nonce': self.web3.eth.get_transaction_count(self.wallet_address), 'data': data_tx}
            if execute_now:
                tx_token = self.execute_transaction(transfer_tx)
                print(f"Updating Position by {position_amount}")
                print(f"TX: {tx_token}")
                time.sleep(1)
                return tx_token
            else:
                return {"token":token_symbol.upper(),'position_size':position_amount/(10**18),'current_position':current_position['size'],"max_leverage":max_leverage/(10**18),"leveraged_percent":(position_amount/max_leverage)*100,"tx_data":transfer_tx}

    # open an order with a specific limit amount
    def open_limit(self, token_symbol: str, limit_price: float, position_amount: float = None, leverage_multiplier: float = None, short: bool = False) -> str:
        """
        Open Limit position in a direction
        ...

        Attributes
        ----------
        token_symbol : str
            token symbol from list of supported asset
        short : bool, optional 
            set to True when creating a short. (Implemented to double check side)
        limit_price : float
            limit price in dollars to open position. 
        position_amount : int, optional 
            position amount in human readable format as trade asset i.e. 12 SOL . Exact position in a direction (Sign this It WILL MATTER).
        leverage_multiplier : 
            Multiplier of Leverage to use when creating order. Based on available margin in account.

        *Use either position_amount or leverage_multiplier.

        Returns
        ----------
        str: token transfer Tx id 
        """
        if (position_amount == None) and (leverage_multiplier == None):
            print("Enter EITHER a position amount or a leverage multiplier!")
            return None
        elif (position_amount != None) and (leverage_multiplier != None):
            print("Enter EITHER a position amount or a leverage multiplier!")
            return None
        current_pos = self.get_current_positions(token_symbol)
        current_price = self.get_current_asset_price(token_symbol)['usd']
        if current_pos['size'] != 0:
            print(f"Already in position! {current_pos['size']/(10**18)}")
            return None
        # Case for position_amount manually set
        if position_amount != None:
            position_amount = position_amount*(10**18)
            if short == True:
                if current_price >= limit_price:
                    return self.open_position(token_symbol, short=True, position_amount=position_amount)
            else:
                if current_price <= limit_price:
                    return self.open_position(token_symbol, short=False, position_amount=position_amount)
        # Case for Leverage Multiplier
        else:
            if short == True:
                if current_price >= limit_price:
                    return self.open_position(token_symbol, short=True, leverage_multiplier=leverage_multiplier)
            else:
                if current_price <= limit_price:
                    return self.open_position(token_symbol, short=False, leverage_multiplier=leverage_multiplier)
        print(
            f"Limit not reached current : {current_price} | Entry: {current_pos['lastPrice']/(10**18)} | Limit: {limit_price}")
        return None

    # Close with Limit

    def close_limit(self, token_symbol: str, limit_price: float, short: bool = False):
        """
        Close Limit position in a direction
        ...

        Attributes
        ----------
        wallet_address : str
            wallet_address of wallet to check
        token_symbol : str
            token symbol from list of supported asset
        short : bool, optional 
            set to True when creating a short. (Implemented to double check side)
        limit_price : float
            limit price in *dollars* to open position. 

        Returns
        ----------
        str: token transfer Tx id 
        """
        current_pos = self.get_current_positions(token_symbol)
        current_price = self.get_current_asset_price(token_symbol)['usd']
        # Check if you are in Position
        if current_pos['size'] == 0:
            print("Not in position!")
            return None
        # Check short value
        if short == True:
            if current_price <= limit_price:
                return self.close_position(token_symbol)
        else:
            if current_price >= limit_price:
                return self.close_position(token_symbol)
        print(
            f"Limit not reached current : {current_price} | Entry: {current_pos['lastPrice']/(10**18)} | Limit: {limit_price}")
        return None

    # Close Order with Stop Limit

    def close_stop_limit(self, token_symbol: str, limit_price: float, stop_price: float, short: bool = False) -> str:
        """
        Close Limit position in a direction with Stop price
        ...

        Attributes
        ----------
        wallet_address : str
            wallet_address of wallet to check
        token_symbol : str
            token symbol from list of supported asset
        short : bool, optional 
            set to True when creating a short. (Implemented to double check side)
        limit_price : float
            limit price in dollars to open position. 
        stop_price : float 
            Set to stop price incase of bad position, will exit position if triggered 

        Returns
        ----------
        str: token transfer Tx id 
        """
        current_pos = self.get_current_positions(token_symbol)
        current_price = self.get_current_asset_price(token_symbol)['usd']
        # Check if you are in Position
        if current_pos['size'] == 0:
            print("Not in position!")
            return None
        # Check short value
        if short == True:
            if current_price <= limit_price:
                return self.close_position(token_symbol)
            elif current_price >= stop_price:
                return self.close_position(token_symbol)
        else:
            if current_price >= limit_price:
                return self.close_position(token_symbol)
            elif current_price <= stop_price:
                return self.close_position(token_symbol)
        print(
            f"Limit not reached current : {current_price} | Entry: {current_pos['lastPrice']/(10**18)} | Limit: {limit_price} | Stop Limit: {stop_price}")
        return None

    def get_historicals(self, token_symbol, time_back=72, period=1800):
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
        url = f'https://api.thegraph.com/subgraphs/name/kwenta/optimism-latest-rates'
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
