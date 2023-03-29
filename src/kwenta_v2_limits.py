#Kwenta-v2-Limits
import pandas as pd
import requests
import random
import numpy as np
import time
from web3 import Web3
import threading
import os
import time
import random
from abi_store import *
from kwenta_config import *
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
import warnings
warnings.filterwarnings('ignore')

web3 = Web3(Web3.HTTPProvider(provider_rpc))

#load SUSD Contract
susd_token = web3.eth.contract(web3.toChecksumAddress(susd_contract['susd_addr']), abi=susd_contract['susd_abi'])

token_list = ['AAVE', 'AP', 'ATOM', 'ARB','AUD', 'AVAX', 'AXS', 'BNB', 'BTC', 'DOGE', 'DYDX', 'ETH', 'EUR', 'FLOW', 'FTM', 'GBP', 'LINK', 'MATIC', 'NEAR', 'OP', 'SOL', 'UNI', 'XAG', 'XAU']

#Load Token Contracts
PerpsV2MarketViews_contract = web3.eth.contract(web3.toChecksumAddress(contracts[base_token]['PerpsV2MarketViews_addr']), abi=contracts[base_token]['PerpsV2MarketViews'])
PerpsV2MarketDelayedOrdersOffchain_contract = web3.eth.contract(web3.toChecksumAddress(contracts[base_token]['ProxyPerpsV2_addr']), abi=contracts[base_token]['PerpsV2MarketDelayedOrdersOffchain'])
ProxyPerpsV2_contract = web3.eth.contract(web3.toChecksumAddress(contracts[base_token]['ProxyPerpsV2_addr']), abi=contracts[base_token]['ProxyPerpsV2'])
PerpsV2MarketState_contract = web3.eth.contract(web3.toChecksumAddress(contracts[base_token]['PerpsV2MarketState_addr']), abi=contracts[base_token]['PerpsV2MarketState'])
PerpsV2Market_contract = web3.eth.contract(web3.toChecksumAddress(contracts[base_token]['ProxyPerpsV2_addr']), abi=contracts[base_token]['PerpsV2Market'])
PerpsV2MarketDelayedOrders_contract = web3.eth.contract(web3.toChecksumAddress(contracts[base_token]['PerpsV2MarketDelayedOrders_addr']), abi=contracts[base_token]['PerpsV2MarketDelayedOrders'])

#Returns bool of if delayed order is in queue
def check_delayed_orders(wallet_address:str) -> bool:
    """
    Check if delayed order is in queue
    ...
    
    Attributes
    ----------
    wallet_address : str
        wallet_address of wallet to check

    """
    return (PerpsV2MarketDelayedOrdersOffchain_contract.functions.delayedOrders(wallet_address).call())[0]

#Returns current asset price
def get_current_asset_price()->dict:
    """
    Gets current asset price for config asset.
    ...
    
    Attributes
    ----------
    None
    
    Returns
    ----------
    Dict with wei and USD price
    """
    wei_price = (PerpsV2MarketViews_contract.functions.assetPrice().call())[0]
    usd_price = wei_price/(10**18)
    return {"usd": usd_price,"wei": wei_price}

#Gets current position data
def get_current_positions(wallet_address:str)->dict:
    """
    Gets Current Position Data
    ...
    
    Attributes
    ----------
    wallet_address : str
        wallet_address of wallet to check

    Returns
    ----------
    Dict: position information
    """
    current_positions = PerpsV2MarketState_contract.functions.positions(wallet_address).call()
    positions_data = {"id":current_positions[0],"lastFundingIndex":current_positions[1],"margin":current_positions[2],"lastPrice":current_positions[3],"size":current_positions[4]}
    return positions_data

#Get margin available for position
def get_accessible_margin(wallet_address:str)->dict:
    """
    Gets available account margin
    ...
    
    Attributes
    ----------
    wallet_address : str
        wallet_address of wallet to check

    Returns
    ----------
    Dict: Margin remaining in wei and usd
    """
    margin_allowed = (PerpsV2MarketViews_contract.functions.accessibleMargin(wallet_address).call())[0]
    readable_amount = margin_allowed /(10**18)
    return {"margin_remaining":margin_allowed,"readable_amount":readable_amount}

#Return bool if Liquidation is possible for wallet
def can_liquidate(wallet_address:str)->dict:
    """
    Checks if Liquidation is possible for wallet
    ...
    
    Attributes
    ----------
    wallet_address : str
        wallet_address of wallet to check

    Returns
    ----------
    Dict: Liquidation Data
    """
    liquidation_check = PerpsV2MarketViews_contract.functions.canLiquidate(wallet_address).call()
    liquidation_price = PerpsV2MarketViews_contract.functions.liquidationPrice(wallet_address).call()
    return {"liq_possible":liquidation_check,"liq_price":liquidation_price}


#Get Current market skew between shorts and longs (useful for determining market difference)
def get_market_skew()->dict:
    """
    Gets current market long/short market skew
    ...
    
    Attributes
    ----------
    None
    
    Returns
    ----------
    Dict with market skew information
    """
    skew = PerpsV2MarketViews_contract.functions.marketSizes().call()
    percent_long = skew[0]/(skew[0]+skew[1])*100
    percent_short = skew[1]/(skew[0]+skew[1])*100
    return {"long":skew[0],"short":skew[1],"percent_long":percent_long,"percent_short":percent_short}

#Gets current SUSD Balance in wallet, NOT MARGIN ACCOUNT
def get_susd_balance(wallet_address:str)->dict:
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
    wei_balance = susd_token.functions.balanceOf(wallet_address).call()
    usd_balance = wei_balance/(10**18)
    return {"wei_balance":wei_balance, "usd_balance":usd_balance}

#Transfers SUSD from wallet to Margin account 
def transfer_margin(token_amount:int,wallet_address:str)->str:
    """
    Transfers SUSD from wallet to Margin account
    ...
    
    Attributes
    ----------
    token_amount : int
        Token amount *in wei* to send to Margin account
    wallet_address : str
        wallet_address of wallet to check

    Returns
    ----------
    str: token transfer Tx id 
    """
    susd_balance = get_susd_balance(wallet_address)    
    print(f"SUSD Available: {susd_balance['usd_balance']}")
    if(token_amount < susd_balance['wei_balance']):
        transfer_tx = PerpsV2Market_contract.functions.transferMargin(token_amount).build_transaction({'from': wallet_address,'gas': 1500000,'gasPrice': web3.toWei('0.4','gwei'),'nonce': web3.eth.get_transaction_count(wallet_address)})
        signed_txn = web3.eth.account.sign_transaction(transfer_tx, private_key=private_key)
        tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print(f"Transferring {susd_balance['usd_balance']} to Account...")
        print(f"TX: {web3.toHex(tx_token)}")
        time.sleep(1)
        return web3.toHex(tx_token)

#Get out amount of leverage available for account
def get_leveraged_amount(leverage_multiplier:float,wallet_address:str)-> dict:
    """
    Get out amount of leverage available for account
    ...
    
    Attributes
    ----------
    leverage_multiplier : int
        leverage multiplier amount. Must be within the range 0.1 - 24.7.
    wallet_address : str
        wallet_address of wallet to check

    Returns
    ----------
    Dict: amount of leverage available and max amount of leverage available
    """
    if leverage_multiplier > 24.7 or leverage_multiplier < 0.1:
        print("Leveraged_multiplier must be within the range 0.1 - 24.7!")
        return None
    susd_balance = get_accessible_margin(wallet_address)
    asset_price = get_current_asset_price()
    print(f"SUSD Available: {susd_balance['readable_amount']}")
    print(f"Current Asset Price: {asset_price['usd']}")
    #Using 24.7 to cover edge cases
    max_leverage = ((susd_balance['readable_amount']/asset_price['usd'])*24.7)*(10**18)
    print(f"Max Leveraged Asset Amount: {max_leverage}")
    leveraged_amount = ((susd_balance['margin_remaining']/asset_price['wei'])*leverage_multiplier)*(10**18)
    return {"leveraged_amount":leveraged_amount,"max_asset_leverage":max_leverage}

#Update current position with new amounts, i.e. increase/decrease position
def update_position(position_amount:int,wallet_address:str)->str:
    """
    Transfers SUSD from wallet to Margin account
    ...
    
    Attributes
    ----------
    position_amount : int
        Position amount *in wei* as trade asset i.e. 12 SOL == 12*(10**18). Exact position in a direction (Sign this It WILL MATTER).
    wallet_address : str
        wallet_address of wallet to check

    Returns
    ----------
    str: token transfer Tx id 
    """
    current_position = get_current_positions(wallet_address)
    print(f"Current Position Size: {current_position['size']}")
    #check that position size is less than margin limit
    if(position_amount < current_position['margin']):
        priceImpactDelta = 500000000000000000
        #HEX for 'KWENTA'
        trackingCode = '0x4b57454e54410000000000000000000000000000000000000000000000000000'
        transfer_tx = PerpsV2MarketDelayedOrdersOffchain_contract.functions.submitOffchainDelayedOrderWithTracking(position_amount,priceImpactDelta,trackingCode).build_transaction({'from': wallet_address,'gas': 1500000,'gasPrice': web3.toWei('0.34','gwei'),'nonce': web3.eth.get_transaction_count(wallet_address)})
        signed_txn = web3.eth.account.sign_transaction(transfer_tx, private_key=private_key)
        tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print(f"Updating Position by {position_amount}")
        print(f"TX: {web3.toHex(tx_token)}")
        time.sleep(1)
        return web3.toHex(tx_token)

#Close full position
def close_position(wallet_address:str)->str:
    """
    Fully closes account position 
    ...
    
    Attributes
    ----------
    wallet_address : str
        wallet_address of wallet to check

    Returns
    ----------
    str: token transfer Tx id 
    """
    current_position = get_current_positions(wallet_address)
    print(f"Current Position Size: {current_position['size']}")
    if current_position['size'] == 0:
        print("Not in position!")
        return None
    #Flip position size to the opposite direction
    position_amount = (current_position['size']) * -1
    #check that position size is less than margin limit
    priceImpactDelta = 500000000000000000
    #HEX for 'KWENTA'
    trackingCode = '0x4b57454e54410000000000000000000000000000000000000000000000000000'
    transfer_tx = PerpsV2MarketDelayedOrdersOffchain_contract.functions.submitOffchainDelayedOrderWithTracking(position_amount,priceImpactDelta,trackingCode).build_transaction({'from': wallet_address,'gas': 1500000,'gasPrice': web3.toWei('0.34','gwei'),'nonce': web3.eth.get_transaction_count(wallet_address)})
    signed_txn = web3.eth.account.sign_transaction(transfer_tx, private_key=private_key)
    tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print(f"Updating Position by {position_amount}")
    print(f"TX: {web3.toHex(tx_token)}")
    time.sleep(1)
    return web3.toHex(tx_token)
    
#Open new Position
def open_position(wallet_address,short:bool=False,position_amount:int=None,leverage_multiplier:float=None)->str:
    """
    Open account position in a direction
    ...
    
    Attributes
    ----------
    wallet_address : str
        wallet_address of wallet to check
    short : bool, optional 
        set to True when creating a short. (Implemented to double check side)
    position_amount : int, optional 
        position amount in wei as trade asset i.e. 12 SOL == 12*(10**18). Exact position in a direction (Sign this It WILL MATTER).
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
    current_position = get_current_positions(wallet_address)
    #starting at zero otherwise use Update position
    if current_position['size'] != 0:
        print(f"You are already in Position, use update_position() instead.")
        print(f"Current Position Size: {(current_position['size'])/(10**18)}")
        return None
    if leverage_multiplier:
        position_amount = get_leveraged_amount(leverage_multiplier,wallet_address)['leveraged_amount']
        #check side
        if short == True:
            position_amount = position_amount * -1
    if (position_amount < 0) and short == False:
        print("Position size is Negative & Short set to False! Double Check intention.")
        return None
    #checking available margin to make sure this is possible
    if(position_amount < get_leveraged_amount(leverage_multiplier,wallet_address)['max_asset_leverage']):
    #check that position size is less than margin limit
        priceImpactDelta = 500000000000000000
        #HEX for 'KWENTA'
        trackingCode = '0x4b57454e54410000000000000000000000000000000000000000000000000000'
        transfer_tx = PerpsV2MarketDelayedOrdersOffchain_contract.functions.submitOffchainDelayedOrderWithTracking(int(position_amount),priceImpactDelta,trackingCode).build_transaction({'from': wallet_address,'gas': 1500000,'gasPrice': web3.toWei('0.34','gwei'),'nonce': web3.eth.get_transaction_count(wallet_address)})
        signed_txn = web3.eth.account.sign_transaction(transfer_tx, private_key=private_key)
        tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print(f"Updating Position by {position_amount}")
        print(f"TX: {web3.toHex(tx_token)}")
        time.sleep(1)
        return web3.toHex(tx_token)


#open an order with a specific limit amount
def open_limit(wallet_address:str,limit_price:float,position_amount:int=None,leverage_multiplier:float=None,short:bool=False)->str:
    """
    Open Limit position in a direction
    ...
    
    Attributes
    ----------
    wallet_address : str
        wallet_address of wallet to check
    short : bool, optional 
        set to True when creating a short. (Implemented to double check side)
    limit_price : float
        limit price in dollars to open position. 
    position_amount : int, optional 
        position amount in wei as trade asset i.e. 12 SOL == 12*(10**18). Exact position in a direction (Sign this It WILL MATTER).
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
    current_pos = get_current_positions(wallet_address)
    current_price = get_current_asset_price()['usd']
    if current_pos['size'] != 0:
        print(f"Already in position! {current_pos['size']/(10**18)}")
        return None
    #Case for position_amount manually set
    if position_amount != None:
        if short == True:
            if current_price >= limit_price:
                return open_position(wallet_address,short=True,position_amount=position_amount)
        else:
            if current_price <= limit_price:
                return open_position(wallet_address,short=False,position_amount=position_amount)
    #Case for Leverage Multiplier
    else:
        if short == True:
            if current_price >= limit_price:
                return open_position(wallet_address,short=True,leverage_multiplier=leverage_multiplier)
        else:
            if current_price <= limit_price:
                return open_position(wallet_address,short=False,leverage_multiplier=leverage_multiplier)
    print(f"Limit not reached current : {current_price} | Entry: {current_pos['lastPrice']/(10**18)} | Limit: {limit_price}")
    return None

#Close with Limit
def close_limit(wallet_address:str,limit_price:float,short:bool=False):
    """
    Close Limit position in a direction
    ...
    
    Attributes
    ----------
    wallet_address : str
        wallet_address of wallet to check
    short : bool, optional 
        set to True when creating a short. (Implemented to double check side)
    limit_price : float
        limit price in *dollars* to open position. 
    
    Returns
    ----------
    str: token transfer Tx id 
    """ 
    current_pos = get_current_positions(wallet_address)
    current_price = get_current_asset_price()['usd']
    #Check if you are in Position
    if current_pos['size'] == 0:
        print("Not in position!")
        return None
    #Check short value
    if short == True:
        if current_price <= limit_price:
            return close_position(wallet_address)
    else:
        if current_price >= limit_price:
            return close_position(wallet_address)
    print(f"Limit not reached current : {current_price} | Entry: {current_pos['lastPrice']/(10**18)} | Limit: {limit_price}")
    return None

#Close Order with Stop Limit
def close_stop_limit(wallet_address:str,limit_price:float,stop_price:float,short:bool=False)->str:
    """
    Close Limit position in a direction with Stop price
    ...
    
    Attributes
    ----------
    wallet_address : str
        wallet_address of wallet to check
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
    current_pos = get_current_positions(wallet_address)
    current_price = get_current_asset_price()['usd']
    #Check if you are in Position
    if current_pos['size'] == 0:
        print("Not in position!")
        return None
    #Check short value
    if short == True:
        if current_price <= limit_price:
            return close_position(wallet_address)
        elif current_price >= stop_price:
            return close_position(wallet_address)
    else:
        if current_price >= limit_price:
            return close_position(wallet_address)
        elif current_price <= stop_price:
            return close_position(wallet_address)
    print(f"Limit not reached current : {current_price} | Entry: {current_pos['lastPrice']/(10**18)} | Limit: {limit_price} | Stop Limit: {stop_price}")
    return None

