import json
import os
import time
import warnings
import random
import pandas as pd
import requests
import numpy as np
from web3 import Web3
from kwenta_sdk.abi_store import *
from kwenta_sdk.kwenta_config import *

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
warnings.filterwarnings('ignore')

class kwenta:
    def __init__(self, provider_rpc:str, wallet_address:str, private_key:str=None):
        #init account variables + contracts
        self.web3 = Web3(Web3.HTTPProvider(provider_rpc))
        self.private_key = private_key
        self.wallet_address = wallet_address
        self.allmarket_listings, self.PerpsV2MarketData_abi, self.PerpsV2Market_abi, self.susd_token = self.init_markets()
        self.token_list = list(self.allmarket_listings.keys())

    def init_markets(self):
        """
        Initializes all market contracts
        ...

        Attributes
        ----------
        N/A
        """
        JSON_PATH = os.path.join(os.path.dirname(__file__), 'json')
        # load the PerpsV2MarketData ABI
        with open(f'{JSON_PATH}\\PerpsV2MarketData.json') as json_file:
            PerpsV2MarketData_abi = json.load(json_file)
        # load the PerpsV2Market ABI
        with open(f'{JSON_PATH}\\PerpsV2Market.json') as json_file:
            PerpsV2Market_abi = json.load(json_file)
        marketdata_contract = self.web3.eth.contract(self.web3.to_checksum_address(
            contracts['PerpsV2MarketData'][10]), abi=PerpsV2MarketData_abi)
        allmarketsdata = (
            marketdata_contract.functions.allProxiedMarketSummaries().call())
        allmarket_listings = {}
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
                "overrideCommitFee": market[10][6]
            }
            allmarket_listings[market[2].decode(
                'utf-8').strip("\x00").strip("PERP")[1:]] = normalized_market

        # load SUSD Contract
        susd_token = self.web3.eth.contract(self.web3.to_checksum_address(susd_contract['susd_addr']), abi=susd_contract['susd_abi'])
        
        return allmarket_listings, PerpsV2MarketData_abi, PerpsV2Market_abi, susd_token

    def load_contracts(self, token_symbol: str):
        """
        Loads contracts for specific token Symbol
        ...

        Attributes
        ----------
        token_symbol : str
            token symbol from list of supported asset
        """
        if not (token_symbol in self.token_list):
            raise Exception("Token Not in Supported Token List.")
        # Load Token Contracts
        proxy_contract = self.web3.eth.contract(self.web3.to_checksum_address(
            self.allmarket_listings[token_symbol]['market_address']), abi=self.PerpsV2Market_abi)
        return proxy_contract

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
        if private_key is None:
            raise Exception("No private key specified.")
        signed_txn = self.web3.eth.account.sign_transaction(
            tx_data, private_key=self.private_key)
        tx_token = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        return self.web3.to_hex(tx_token)

    # Returns bool of if delayed order is in queue
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
        contracts = self.load_contracts(token_symbol.upper())
        return (contracts.functions.delayedOrders(self.wallet_address).call())[0]

    # Returns current asset price

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
        contracts = self.load_contracts(token_symbol.upper())
        wei_price = (contracts.functions.assetPrice().call())[0]
        usd_price = wei_price/(10**18)
        return {"usd": usd_price, "wei": wei_price}

    # Gets current position data

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
        contracts = self.load_contracts(token_symbol.upper())
        current_positions = contracts.functions.positions(
            self.wallet_address).call()
        current_asset_price = self.get_current_asset_price(token_symbol)
        if current_positions[4] < 0:
            pnl = abs(current_asset_price['usd']* (current_positions[3]/(10**18))) - abs((current_positions[2]/(10**18))*(current_positions[3]/(10**18)))
        else:
            pnl = abs((current_positions[2]/(10**18))*(current_positions[3]/(10**18))) - abs(current_asset_price['usd']* (current_positions[3]/(10**18)))
        positions_data = {"id": current_positions[0], "lastFundingIndex": current_positions[1],
                          "margin": current_positions[2], "lastPrice": current_positions[3], "size": current_positions[4],"pnl_usd": pnl}
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
        contracts = self.load_contracts(token_symbol.upper())
        margin_allowed = (contracts.functions.accessibleMargin(
            self.wallet_address).call())[0]
        readable_amount = margin_allowed / (10**18)
        return {"margin_remaining": margin_allowed, "readable_amount": readable_amount}

    # Return bool if Liquidation is possible for wallet

    def can_liquidate(self, token_symbol: str) -> dict:
        """
        Checks if Liquidation is possible for wallet
        ...

        Attributes
        ----------
        wallet_address : str
            wallet_address of wallet to check
        token_symbol : str
            token symbol from list of supported asset
        Returns
        ----------
        Dict: Liquidation Data
        """
        contracts = self.load_contracts(token_symbol.upper())
        liquidation_check = contracts.functions.canLiquidate(
            self.wallet_address).call()
        liquidation_price = contracts.functions.liquidationPrice(
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
        contracts = self.load_contracts(token_symbol.upper())
        skew = contracts.functions.marketSizes().call()
        percent_long = skew[0]/(skew[0]+skew[1])*100
        percent_short = skew[1]/(skew[0]+skew[1])*100
        return {"long": skew[0], "short": skew[1], "percent_long": percent_long, "percent_short": percent_short}

    # Gets current SUSD Balance in wallet, NOT MARGIN ACCOUNT

    def get_susd_balance(self) -> dict:
        """
        Gets current SUSD Balance in wallet
        ...

        Attributes
        ----------
        wallet_address : str
            wallet_address of wallet to check
        Returns
        ----------
        Dict: wei and usd SUSD balance
        """
        wei_balance = self.susd_token.functions.balanceOf(self.wallet_address).call()
        usd_balance = wei_balance/(10**18)
        return {"wei_balance": wei_balance, "usd_balance": usd_balance}

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
        token_amount = (token_amount)*(10**18)
        susd_balance = self.get_susd_balance()
        contracts = self.load_contracts(token_symbol.upper())
        print(f"SUSD Available: {susd_balance['usd_balance']}")
        if (token_amount < susd_balance['wei_balance']):
            data_tx = contracts.encodeABI(
                fn_name='transferMargin', args=[token_amount])
            transfer_tx = {'value': 0, 'chainId': 10, 'to': contracts.address, 'from': self.wallet_address, 'gas': 1500000,
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
        leverage_multiplier : int
            leverage multiplier amount. Must be within the range 0.1 - 24.7.
        wallet_address : str
            wallet_address of wallet to check
        token_symbol : str
            token symbol from list of supported asset

        Returns
        ----------
        Dict: amount of leverage available and max amount of leverage available
        """
        if leverage_multiplier != None:
            if leverage_multiplier > 24.7 or leverage_multiplier < 0.1:
                print("Leveraged_multiplier must be within the range 0.1 - 24.7!")
                return None
        susd_balance = self.get_accessible_margin(token_symbol)
        asset_price = self.get_current_asset_price(token_symbol)
        print(f"SUSD Available: {susd_balance['readable_amount']}")
        print(f"Current Asset Price: {asset_price['usd']}")
        # Using 24.7 to cover edge cases
        max_leverage = (
            (susd_balance['readable_amount']/asset_price['usd'])*24.7)*(10**18)
        print(f"Max Leveraged Asset Amount: {max_leverage}")
        leveraged_amount = (
            (susd_balance['margin_remaining']/asset_price['wei'])*leverage_multiplier)*(10**18)
        return {"leveraged_amount": leveraged_amount, "max_asset_leverage": max_leverage}

    # Update current position with new amounts, i.e. increase/decrease position

    def update_position(self, token_symbol: str, position_amount: float,execute_now:bool=False) -> str:
        """
        Transfers SUSD from wallet to Margin account
        ...

        Attributes
        ----------
        position_amount : float
            Position amount *in human readable* as trade asset i.e. 12 SOL == 12*(10**18). Exact position in a direction (Sign this It WILL MATTER).
        token_symbol : str
            token symbol from list of supported asset
        wallet_address : str
            wallet_address of wallet to check

        Returns
        ----------
        str: token transfer Tx id 
        """
        contracts = self.load_contracts(token_symbol.upper())
        position_amount = position_amount*(10**18)
        current_position = self.get_current_positions(token_symbol)
        print(f"Current Position Size: {current_position['size']}")
        # check that position size is less than margin limit
        if (position_amount < current_position['margin']):
            priceImpactDelta = 500000000000000000
            # HEX for 'KWENTA'
            trackingCode = '0x4b57454e54410000000000000000000000000000000000000000000000000000'
            data_tx = contracts.encodeABI(fn_name='submitOffchainDelayedOrderWithTracking', args=[
                int(position_amount), priceImpactDelta, trackingCode])
            transfer_tx = {'value': 0, 'chainId': 10, 'to': contracts.address, 'from': self.wallet_address, 'gas': 1500000,
                           'gasPrice': self.web3.to_wei('0.4', 'gwei'), 'nonce': self.web3.eth.get_transaction_count(self.wallet_address), 'data': data_tx}
            if execute_now:
                tx_token = self.execute_transaction(transfer_tx)
                print(f"Updating Position by {position_amount}")
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
        wallet_address : str
            wallet_address of wallet to check
        token_symbol : str
            token symbol from list of supported asset

        Returns
        ----------
        str: token transfer Tx id 
        """
        contracts = self.load_contracts(token_symbol.upper())
        current_position = self.get_current_positions(token_symbol)
        print(f"Current Position Size: {current_position['size']}")
        if current_position['size'] == 0:
            print("Not in position!")
            return None
        # Flip position size to the opposite direction
        position_amount = (current_position['size']) * -1
        # check that position size is less than margin limit
        priceImpactDelta = 500000000000000000
        # HEX for 'KWENTA'
        trackingCode = '0x4b57454e54410000000000000000000000000000000000000000000000000000'
        data_tx = contracts.encodeABI(fn_name='submitOffchainDelayedOrderWithTracking', args=[
            int(position_amount), priceImpactDelta, trackingCode])
        transfer_tx = {'value': 0, 'chainId': 10, 'to': contracts.address, 'from': self.wallet_address, 'gas': 1500000,
                       'gasPrice': self.web3.to_wei('0.4', 'gwei'), 'nonce': self.web3.eth.get_transaction_count(self.wallet_address), 'data': data_tx}
        if execute_now:
            tx_token = self.execute_transaction(transfer_tx)
            print(f"Updating Position by {position_amount}")
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
        wallet_address : str
            wallet_address of wallet to check
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
        contracts = self.load_contracts(token_symbol.upper())
        # starting at zero otherwise use Update position
        if current_position['size'] != 0:
            print(f"You are already in Position, use update_position() instead.")
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
            # check that position size is less than margin limit
            priceImpactDelta = 500000000000000000
            # HEX for 'KWENTA'
            trackingCode = '0x4b57454e54410000000000000000000000000000000000000000000000000000'
            data_tx = contracts.encodeABI(fn_name='submitOffchainDelayedOrderWithTracking', args=[
                int(position_amount), priceImpactDelta, trackingCode])
            transfer_tx = {'value': 0, 'chainId': 10, 'to': contracts.address, 'from': self.wallet_address, 'gas': 1500000,
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
        wallet_address : str
            wallet_address of wallet to check
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
