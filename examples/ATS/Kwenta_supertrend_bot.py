# Kwenta SDK Trading Bot Example
# Example ATS with trading the supertrend using the Kwenta SDK
# Trading Bot Disclaimer: Use our trading bot at your own risk. We do not guarantee profits or accuracy of the bot's decisions. 
# Trading in financial markets carries inherent risks, and you are solely responsible for your trading decisions. 
# We are not liable for any losses or damages resulting from the use of our trading bot.
# Please consult with a qualified financial advisor before making any investment decisions.
# Sleeps are required to ensure execution

########################################################################
'''
General Function + Information
1. Asset Price Checking happens in separate thread from main thread. This is to catch price triggers out of band of the main strat
2. Tweak the parameters in the MAIN function and the run_strat function to your liking. The defaults are for reference. 
3. General Flow:
    Run strat: 5mins
    Strat triggers open position
    Check position Price every 1 second for "percent trigger"
    Every 5mins strat will run to check for closing opportunity. (There is profit limits added into the strat, change those to something that makes sense)
    If price trigger or strat trigger, close position and withdrawal margin from account if necessary. (Pull out withdrawal if you do not want it automatically done.)
    
4. This bot is meant to be used as a reference for what can be done with the Kwenta SDK. There are many optimizations that can be made and an infinite amount of customization that can be added. This is your easel, paint within the lines. 
'''
#########################################################################
from kwenta import Kwenta
import time
import pandas_ta as ta
import asyncio
import pandas as pd
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
import warnings
warnings.filterwarnings('ignore')
import schedule
import threading
import sys
#calculate True Range
def tr(data):
    data['previous_close'] = data['close'].shift(1)
    data['high-low'] = abs(data['high'] - data['low'])
    data['high-pc'] = abs(data['high'] - data['previous_close'])
    data['low-pc'] = abs(data['low'] - data['previous_close'])
    tr = data[['high-low', 'high-pc', 'low-pc']].max(axis=1)
    return tr

#Calculate Average True Range
def atr(data, period):
    data['tr'] = tr(data)
    atr = data['tr'].rolling(period).mean()
    return atr

#calculate SuperTrend
def supertrend(df, period=18, atr_multiplier=2):
    hl2 = (df['high'] + df['low']) / 2
    df['atr'] = atr(df, period)
    df['upperband'] = hl2 + (atr_multiplier * df['atr'])
    df['lowerband'] = hl2 - (atr_multiplier * df['atr'])
    df['in_uptrend'] = True
    for current in range(1, len(df.index)):
        previous = current - 1
        if df['close'][current] > df['upperband'][previous]:
            df['in_uptrend'][current] = True
        elif df['close'][current] < df['lowerband'][previous]:
            df['in_uptrend'][current] = False
        else:
            df['in_uptrend'][current] = df['in_uptrend'][previous]
            if df['in_uptrend'][current] and df['lowerband'][current] < df['lowerband'][previous]:
                df['lowerband'][current] = df['lowerband'][previous]
            if not df['in_uptrend'][current] and df['upperband'][current] > df['upperband'][previous]:
                df['upperband'][current] = df['upperband'][previous]
    return df 

#calculate Triple SuperTrend
def triplesupertrend(df, period1=16, period2 =17, period3 = 18, atr_multiplier1=1, atr_multiplier2=2, atr_multiplier3 = 3):
    hl2 = (df['high'] + df['low']) / 2
    df['atr1'] = atr(df, period1)
    df['atr2'] = atr(df, period2)
    df['atr3'] = atr(df, period3)
    df['upperband1'] = hl2 + (atr_multiplier1 * df['atr1'])
    df['lowerband1'] = hl2 - (atr_multiplier1 * df['atr1'])
    df['in_uptrend1'] = True
    df['upperband2'] = hl2 + (atr_multiplier2 * df['atr2'])
    df['lowerband2'] = hl2 - (atr_multiplier2 * df['atr2'])
    df['in_uptrend2'] = True
    df['upperband3'] = hl2 + (atr_multiplier3 * df['atr3'])
    df['lowerband3'] = hl2 - (atr_multiplier3 * df['atr3'])
    df['in_uptrend3'] = True
    for current in range(1, len(df.index)):
        previous = current - 1
#trend1
        if df['close'][current] > df['upperband1'][previous]:
            df['in_uptrend1'][current] = True
        elif df['close'][current] < df['lowerband1'][previous]:
            df['in_uptrend1'][current] = False
        else:
            df['in_uptrend1'][current] = df['in_uptrend1'][previous]
            if df['in_uptrend1'][current] and df['lowerband1'][current] < df['lowerband1'][previous]:
                df['lowerband1'][current] = df['lowerband1'][previous]
            if not df['in_uptrend1'][current] and df['upperband1'][current] > df['upperband1'][previous]:
                df['upperband1'][current] = df['upperband1'][previous]
#trend2
        if df['close'][current] > df['upperband2'][previous]:
            df['in_uptrend2'][current] = True
        elif df['close'][current] < df['lowerband2'][previous]:
            df['in_uptrend2'][current] = False
        else:
            df['in_uptrend2'][current] = df['in_uptrend2'][previous]
            if df['in_uptrend2'][current] and df['lowerband2'][current] < df['lowerband2'][previous]:
                df['lowerband2'][current] = df['lowerband2'][previous]
            if not df['in_uptrend2'][current] and df['upperband2'][current] > df['upperband2'][previous]:
                df['upperband2'][current] = df['upperband2'][previous]
#Trend3 
        if df['close'][current] > df['upperband3'][previous]:
            df['in_uptrend3'][current] = True
        elif df['close'][current] < df['lowerband3'][previous]:
            df['in_uptrend3'][current] = False
        else:
            df['in_uptrend3'][current] = df['in_uptrend3'][previous]
            if df['in_uptrend3'][current] and df['lowerband3'][current] < df['lowerband3'][previous]:
                df['lowerband3'][current] = df['lowerband3'][previous]
            if not df['in_uptrend3'][current] and df['upperband3'][current] > df['upperband3'][previous]:
                df['upperband3'][current] = df['upperband3'][previous]
    return df 

#calculate Pivot Points
#will need at least 1 day's worth of closing pricing
def PivotPoint(high,low,close):
    Pivot = (high + low + close)/3
    R1 = 2*Pivot - low
    S1= 2*Pivot - high
    R2 = Pivot + (high - low)
    S2 = Pivot - (high - low)
    R3 = Pivot + 2*(high - low)
    S3 = Pivot - 2*(high - low)
    return Pivot,S3,S2,S1,R1,R2,R3

# Advanced Pivot grid. Not implemented, but available to use. 
def pivotGrid(last_second_price,df):
    last_row_index = len(df.index) - 1
    pivotmid = (df['Pivot'][last_row_index]+df['R1'][last_row_index])/2
    pivotlowmid = (df['Pivot'][last_row_index]+pivotmid)/2
    pivothighmid = (df['R1'][last_row_index]+pivotmid)/2
    if(last_second_price > df['Pivot'][last_row_index] and last_second_price < pivotlowmid):
        pivot_price = df["Pivot"][last_row_index]
    elif(last_second_price > pivotlowmid and last_second_price < pivotmid):
        pivot_price = pivotlowmid
    elif(last_second_price > pivotmid and last_second_price < pivothighmid):
        pivot_price = pivotmid
    elif(last_second_price > pivothighmid and last_second_price < df['R1'][last_row_index]):
        pivot_price = pivothighmid
    else:
        pivotmid = (df['R1'][last_row_index]+df['R2'][last_row_index])/2
        pivotlowmid = (df['R1'][last_row_index]+pivotmid)/2
        pivothighmid = (df['R2'][last_row_index]+pivotmid)/2
        if(last_second_price > df['R1'][last_row_index] and last_second_price < pivotlowmid):
                pivot_price = df["R1"][last_row_index]
        elif(last_second_price > pivotlowmid and last_second_price < pivotmid):
            pivot_price = pivotlowmid
        elif(last_second_price > pivotmid and last_second_price < pivothighmid):
            pivot_price = pivotmid
        elif(last_second_price > pivothighmid and last_second_price < df['R2'][last_row_index]):
            pivot_price = pivothighmid
        else:
            pivotmid = (df['R2'][last_row_index]+df['R3'][last_row_index])/2
            pivotlowmid = (df['R2'][last_row_index]+pivotmid)/2
            pivothighmid = (df['R3'][last_row_index]+pivotmid)/2
            if(last_second_price > df['R2'][last_row_index] and last_second_price < pivotlowmid):
                    pivot_price = df["R2"][last_row_index]
            elif(last_second_price > pivotlowmid and last_second_price < pivotmid):
                pivot_price = pivotlowmid
            elif(last_second_price > pivotmid and last_second_price < pivothighmid):
                pivot_price = pivotmid
            elif(last_second_price > pivothighmid and last_second_price < df['R3'][last_row_index]):
                pivot_price = pivothighmid
            elif(last_second_price > df['R3'][last_row_index]):
                pivot_price = df['R3'][last_row_index]
            else:
                pivotmid = (df['Pivot'][last_row_index]+df['S1'][last_row_index])/2
                pivotlowmid = (df['S1'][last_row_index]+pivotmid)/2
                pivothighmid = (df['Pivot'][last_row_index]+pivotmid)/2
                if(last_second_price < df['Pivot'][last_row_index] and  last_second_price > pivothighmid):
                    pivot_price = df["Pivot"][last_row_index]
                elif(last_second_price < pivothighmid and last_second_price > pivotmid):
                    pivot_price = pivothighmid
                elif(last_second_price < pivotmid and last_second_price > pivotlowmid):
                    pivot_price = pivotmid
                elif(last_second_price < pivotlowmid and last_second_price > df['S2'][last_row_index]):
                    pivot_price = pivotlowmid
                else:
                    pivotmid = (df['S1'][last_row_index]+df['S2'][last_row_index])/2
                    pivotlowmid = (df['S2'][last_row_index]+pivotmid)/2
                    pivothighmid = (df['S1'][last_row_index]+pivotmid)/2
                    if(last_second_price < df['S1'][last_row_index] and  last_second_price > pivothighmid):
                        pivot_price = df["S1"][last_row_index]
                    elif(last_second_price < pivothighmid and last_second_price > pivotmid):
                        pivot_price = pivothighmid
                    elif(last_second_price < pivotmid and last_second_price > pivotlowmid):
                        pivot_price = pivotmid
                    elif(last_second_price < pivotlowmid and last_second_price > df['S3'][last_row_index]):
                        pivot_price = pivotlowmid
                    else:
                        pivotmid = (df['S2'][last_row_index]+df['S3'][last_row_index])/2
                        pivotlowmid = (df['S3'][last_row_index]+pivotmid)/2
                        pivothighmid = (df['S2'][last_row_index]+pivotmid)/2
                        if(last_second_price < df['S2'][last_row_index] and  last_second_price > pivothighmid):
                            pivot_price = df["S2"][last_row_index]
                        elif(last_second_price < pivothighmid and last_second_price > pivotmid):
                            pivot_price = pivothighmid
                        elif(last_second_price < pivotmid and last_second_price > pivotlowmid):
                            pivot_price = pivotmid
                        elif(last_second_price < pivotlowmid and last_second_price > df['S3'][last_row_index]):
                            pivot_price = pivotlowmid
                        elif(last_second_price < df['S3'][last_row_index]):
                            pivot_price = df['S3'][last_row_index]
    return pivot_price

#Run all strategies and collect data into frame
def run_strat():
    global strat_data
    candles_df = asyncio.run(get_candle_data())
    triple_trend_period1 = 19
    triple_trend_period2 = 20
    triple_trend_period3 = 23
    atr_multiplier1 =1.5
    atr_multiplier2 =2
    atr_multiplier3 =2.5
    macd_fast = 14
    macd_slow = 18
    macd_signal = 6 
    try:
        strat_data = triplesupertrend(candles_df, period1=triple_trend_period1 ,period2=triple_trend_period2,period3=triple_trend_period3, atr_multiplier1=atr_multiplier1, atr_multiplier2=atr_multiplier2, atr_multiplier3 = atr_multiplier3)
    except Exception as e:
        print(e)
        print("Failed to calculate triplesupertrend.")
    #Use MACDAS thank you Tradingview
    try:
        strat_data.ta.macd(close='close', fast=macd_fast, slow=macd_slow, signal=macd_signal, append=True,asmode='True')
        strat_data.rename(columns = {f'MACDAS_{macd_fast}_{macd_slow}_{macd_signal}':'macd', f'MACDASh_{macd_fast}_{macd_slow}_{macd_signal}':'hist',f'MACDASs_{macd_fast}_{macd_slow}_{macd_signal}':'signal'}, inplace = True)
    except Exception as e:
        print(e)
        print("Error Calculating MACD, Wait for More Data to Populate...")
    #calculate the last period Pivot Points -- Works Better if you calculate this with a day timeframe. (generate a second set of candles) 
    try:    
        strat_data['Pivot'],strat_data['S3'],strat_data['S2'],strat_data['S1'],strat_data['R1'],strat_data['R2'],strat_data['R3'] = PivotPoint(candles_df.tail(1)["high"],candles_df.tail(1)["low"],candles_df.tail(1)["close"])
    except Exception as e:
        print(e)
        print("Error Calculating Pivot Points, Wait for More Data to Populate...")

#Checks Asset price for profit target percent
def check_asset_price():
    global in_position, entry_price, supertrendFlip, profit_percent
    while True:
        try:
            asset_price = float(account.get_current_asset_price(market)['usd'])
            print(f"Current {market} sUSD Price: {asset_price} | in_position: {in_position}")
            if in_position:
                #calculate percent profit from entry
                position_pnl = float(account.get_current_position(market, wallet_address=smaccount)['pnl_usd']) 
                profit_percent = (position_pnl/amountin)*100
                print(f"Current {market} sUSD Price: {asset_price} | in_position: {in_position} | Position PNL: {position_pnl}")
                if (profit_percent <= (stop_percent_target*-1)):
                    print("Percent Stop Loss Hit! Time to sell...")
                    if not (account.check_delayed_orders(market)['is_open']):
                        account.close_position(market, smaccount, execute_now=True)
                        print("Position Closed, waiting for account to settle...")
                        in_position = False
                        supertrendFlip = False
                        print("Position Stop Loss hit. Stopping execution... ")
                        sys.exit(0)
                if (profit_percent >= profit_percent_target):
                    print("Percent Profit Hit! Time to sell...")
                    if not (account.check_delayed_orders(market)['is_open']):
                        account.close_position(market, smaccount, execute_now=True)
                        print("Position Closed, waiting for account to settle...")
                        in_position = False
                        supertrendFlip = False
                        time.sleep(10)
                        margin_in_account = (account.get_current_position(market, wallet_address=smaccount)['margin'])/(10**18)
                        print(f'Margin in {market} market: {margin_in_account}')
                        if margin_in_account > withdrawal_limit:
                            #withdraw limit amount less amountin+10 so strat can keep running. +10 covers cost variances of usd
                            account.withdrawal_margin(market, token_amount=(margin_in_account-(withdrawal_limit-(amountin+10))*-1), withdrawal_all=False, execute_now=True)
                            time.sleep(4)
        except:
            print("Network error, attempting price grab again...")
        time.sleep(1)

#check start collection for execution signal
def check_signals():
    print(f"Checking Signals For Market: {market}")
    global entry_price, in_position, supertrendFlip
    last_row_index = len(strat_data.index) - 1
    previous_row_index = last_row_index - 1           
    ################################################################
    #check for flip both green - red and red - green
    if ((strat_data['in_uptrend1'][last_row_index] or strat_data['in_uptrend2'][last_row_index]) and (not strat_data['in_uptrend1'][previous_row_index] or not strat_data['in_uptrend2'][previous_row_index]) or (not strat_data['in_uptrend1'][last_row_index] or not strat_data['in_uptrend2'][last_row_index]) and (strat_data['in_uptrend1'][previous_row_index] or strat_data['in_uptrend2'][previous_row_index])):
        supertrendFlip = True
    print(f"SuperTrendflip is {supertrendFlip}")
    ################################################################
    ##### BUYING #################################
    #Actual Strat Check -- This strat only longs, but could be reversed for short entries ;) 
    # Possible Scenarios:
    # 1. Triple Supertrend 1 and 2 in uptrend, (confirms uptrend)
    if ((strat_data['in_uptrend2'][last_row_index] and strat_data['in_uptrend1'][last_row_index])):
        print("In Uptrend")
        print(strat_data.iloc[last_row_index])
        print(f"SuperTrend Signal: {strat_data['in_uptrend2'][last_row_index] and strat_data['in_uptrend1'][last_row_index]}")
        if not in_position:
            usd_balance = int(account.get_current_position(market, wallet_address=smaccount)['margin'])
            if amountin > usd_balance:
                print("Insufficient Amount in Wallet!")
                raise Exception("Insufficient Amount in Wallet!")
            else:
                print(f"Opening {amountin*leverage_multiplier} USD Position in {market} Market.")
                account.open_position(market, smaccount, short=False, leverage_multiplier=leverage_multiplier, execute_now=True)
                in_position = True
                supertrendFlip = False
                entry_price = float(account.get_current_asset_price(market)['usd'])
        else:
            print(f"Already in position in {market}, nothing to do.")
    ################################################################
    ##### Selling #################################
    #Sell if supertrend 1 has flipped  and is now negative
    elif ((not strat_data['in_uptrend1'][last_row_index]) and supertrendFlip is True):
        if in_position:
            if profit_percent < 2:
                print(f"Downtrend Detected, but base profit percentage not hit. Keeping position open... | Current Profit Percentage: {profit_percent}")
                pass
            print("SuperTrend downtrend, time to sell...")
            print(strat_data.iloc[last_row_index])
            if not (account.check_delayed_orders(market)['is_open']):
                account.close_position(market, smaccount, execute_now=True)
                print("Position Closed, waiting for account to settle...")
                in_position = False
                supertrendFlip = False
                time.sleep(10)
                margin_in_account = (account.get_current_position(market, wallet_address=smaccount)['margin'])/(10**18)
                print(f'Margin in {market} market: {margin_in_account}')
                if margin_in_account > withdrawal_limit:
                    #withdraw limit amount less amountin+10 so strat can keep running. +10 covers cost variances of usd
                    account.withdrawal_margin(market, token_amount=(margin_in_account-(withdrawal_limit-(amountin+10))*-1), withdrawal_all=False, execute_now=True)
                    time.sleep(4)
    else:
        print(f"Waiting for Entry... ")
                    
async def get_candle_data():
    global candles_df
    #5min timeframe, 72 hours back
    candles_df = await account.queries.candles(market,time_back=180, period=300)
    candles_df['open'] = candles_df['open'].astype(float)
    candles_df['close'] = candles_df['close'].astype(float)
    candles_df['high'] = candles_df['high'].astype(float)
    candles_df['low'] = candles_df['low'].astype(float)
    return candles_df

if __name__ == "__main__":
    global account, in_position, supertrendFlip, macdCross, smaccount, usd_balance, market, amountin, leverage_multiplier, candles_df, profit_percent_target
    #######################################
    # VARIABLES
    #######################################
    provider_rpc = "Provider_rpc"
    wallet_address = "EOA_WALLET_ADDRESS"
    private_key = "PRIVATE_KEY"
    market = "UPPER_CASE_MARKET_SYMBOL"
    amountin  = 500
    withdrawal_limit = 1500
    leverage_multiplier = 5
    profit_percent_target = 10
    stop_percent_target = 20
    in_position= False
    supertrendFlip = False
    macdCross = False
    ########################
    print("Initializing Kwenta Account...")
    account = Kwenta(provider_rpc=provider_rpc, wallet_address=wallet_address, private_key=private_key)
    candles_df = asyncio.run(get_candle_data())
    smaccount = account.get_sm_accounts()[0]
    eoa_usd_balance = account.get_susd_balance(wallet_address)['balance_usd']
    current_pos = account.get_current_position(market, wallet_address=smaccount)
    # Run below to withdrawal all from market
    # account.withdrawal_margin(market, token_amount=-1, withdrawal_all=True, execute_now=True)
    # account.transfer_margin(market, -1, withdrawal_all=True, execute_now=True)
    if amountin > eoa_usd_balance:
        print("Insufficient Amount in Wallet! Adding Margin to Account")
        raise Exception("Insufficient sUSD Amount in EOA Wallet!")
    elif (current_pos['size']) != 0:
        raise Exception("Already In Position, Please close any open positions before running!")
    elif (current_pos['margin'])/(10**18) > amountin:
        print("Market Margin Sufficent. Starting Market Monitor...")
    else:
        #calculate amountin based on current holdings in SM account
        transfer_amount = (amountin - (current_pos['margin'])/(10**18))+5
        account.transfer_margin(market, transfer_amount, execute_now=True)
    time.sleep(4)
    #######################################################################
    #Start Price Data Thread
    getPrice_thread = threading.Thread(target=check_asset_price,)
    getPrice_thread.daemon = True
    getPrice_thread.start()
        
    # Run the Candle getter every X seconds
    # Sync this to the candle stick Period time
    schedule.every(330).seconds.do(run_strat)
    schedule.every(340).seconds.do(check_signals)
    while True:
        schedule.run_pending()
        time.sleep(1)

