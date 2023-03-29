#Streamlit Kwenta Dashboard
import streamlit as st
import pandas as pd
import base64
import numpy as np
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width',250)
import warnings
warnings.filterwarnings('ignore')
import json
import traceback
import time 
import ssl 
import sys
#import from main folder
sys.path.append("../")
from kwenta_v2_sdk import *
from abi_store import *
from draw_candles import get_candlestick_plot_simple
import requests
import time
import streamlit.components.v1 as components
from streamlit.runtime.scriptrunner.script_run_context import get_script_run_ctx,add_script_run_ctx
import threading


#get account info from Kwenta Graph API
def get_account_info(wallet_address):
    url = f'https://subgraph.satsuma-prod.com/05943208e921/kwenta/optimism-perps/api'
    headers = {'origin':'https://kwenta.eth.limo',
               'referer': 'http://kwenta.eth.limo',
               'accept':'application/json',
               'content-type':'application/json'}
    query = f'''{{futuresPositions(where:{{account:\"{wallet_address}\"}},first:1000,orderBy:\"openTimestamp\",orderDirection:\"desc\"){{id lastTxHash openTimestamp closeTimestamp timestamp market marketKey asset account abstractAccount accountType isOpen isLiquidated trades totalVolume size initialMargin margin pnl feesPaid netFunding pnlWithFeesPaid netTransfers totalDeposits fundingIndex entryPrice avgEntryPrice lastPrice exitPrice}}}}'''
    payload ={
        "query": query    
    }
    try:
        response = requests.post(url,headers=headers,json=payload)
        return response.json()
    except Exception as e:
        print(e)
        return None


st.set_page_config(layout='wide',page_title="Kwenta-V2",page_icon=":shopping_trolley:")
#BUILDING WEBPAGE
st.sidebar.title("KWENTA PERPS")
st.sidebar.header("Token")
endpoint_choices = ["Solana","Optimism"]
endpoint = st.sidebar.selectbox("Choose a Token", endpoint_choices)
st.sidebar.header("Wallet Address")
st.sidebar.write(f"{wallet_address}")

# Working on Building automatic dashboard refresh
# # a flag to allow us to stop the main thread on shut down
# run_thread = True
# # when shutdown is started, set the flag to false
# def shutdown():
#     global run_thread
#     run_thread = False
    
# def update_dashboard():
#     global df
#     while run_thread:
#         # show the spinner while we wait for data
#         with st.spinner('Loading data..'):
#             while local_df is None or:
#                 time.sleep(0.2) # wait a moment for more data to arrive
#                 local_df = df.copy(deep=True) # copy reference, so df can b
#         with placeholder.container():
#             st.markdown("### Chart Title")
#             st.line_chart(local_df[["datetime", 'Speed', 'EngineRPM']].set_index("datetime"))
#             st.dataframe(local_df)
#         time.sleep(1)

# # setup the thread to update the ui
# ui_updater_thread = threading.Thread(target=update_dashboard)
# add_script_run_ctx(ui_updater_thread)
# ui_updater_thread.start()

if (endpoint == "Solana"):
    st.title("Kwenta - Solana")
    token = "SOL"
    account_data = get_account_info(wallet_address)['data']['futuresPositions'][0]
    # st.write(account_data)
    col1, col2, col3, col4= st.columns(4)
    current_position = get_current_positions(wallet_address)
    #general Account Data
    if current_position['size'] == 0:
        col1.metric("Current Position", current_position['size'], "0",delta_color="off")
        col2.metric("Entry Price", "0", "0",delta_color="off")
        col3.metric("Current Price", get_current_asset_price()['usd'], "0",delta_color="off")
        col4.metric("Current Margin",(get_accessible_margin(wallet_address)['readable_amount']),delta_color="off")
    else:
        col1.metric("Current Position", int(current_position['size'])/(10**18), f"PNL: {((get_current_asset_price()['usd'])-(int(account_data['entryPrice'])/(10**18)))*int(current_position['size'])/(10**18)}",delta_color="off")
        col2.metric("Entry Price",int(account_data['entryPrice'])/(10**18),((get_current_asset_price()['usd'])-(int(account_data['entryPrice'])/(10**18))),delta_color="off")
        col3.metric("Current Price", get_current_asset_price()['usd'], "0",delta_color="off")
        col4.metric("Current Margin",(get_accessible_margin(wallet_address)['readable_amount']),delta_color="off")
    
    #Close Position Button - Useful for Instant OUT
    with col1:
        if current_position['size'] == 0:
            close_button = st.button("Close Position",disabled=True,key="close_pos",use_container_width=True)
        else:
            close_button = st.button("Close Position",key="close_pos")
    #Close Position 
    if close_button:
        close_position(wallet_address)
        st.success("Position Closed")
        
    tcol1, tcol2 = st.columns(2)
    ############################################
    #LONG TRADES
    with tcol1:
        # Amount input
        st.subheader("Long Trade")
        if 'long_amount' not in st.session_state:
            st.session_state.long_amount = 0.0
        if 'long_multiplier' not in st.session_state:
            st.session_state.long_multiplier = 0.0
        if 'long_order_type' not in st.session_state:
            st.session_state.long_order_type = "Buy_Limit_Order"
        if 'long_limit' not in st.session_state:
            st.session_state.long_limit = get_current_asset_price()['usd']
        if 'long_stop_limit' not in st.session_state:
            st.session_state.long_stop_limit = get_current_asset_price()['usd']*(0.96)
        
        def refresh_values(long_amount,long_multiplier,long_order_type,long_limit,long_stop_limit):
            st.session_state.long_amount = long_amount
            st.session_state.long_multiplier = long_multiplier
            st.session_state.long_order_type = long_order_type
            st.session_state.long_limit = long_limit
            st.session_state.long_stop_limit = long_stop_limit
            
        long_amount = st.number_input("Margin Amount (Leave at 0 to use leverage multiplier)", value=st.session_state.long_amount,min_value=0.0,max_value=get_leveraged_amount(24.7,wallet_address)['max_asset_leverage']/(10**18), step=10.0,key="long_amount")
        # Slider for liquidation multiplier
        long_multiplier = st.number_input("Liquidation Multiplier",value= st.session_state.long_multiplier, step=1.0,key="long_multiplier")
        # Limit order dropdown
        long_order_type = st.selectbox("Order Type", ["Buy_Limit_Order", "Sell_Limit_Order"],key="long_order_type")
        # Amount input for limit order
        long_limit = st.number_input("Limit Price", value=st.session_state.long_limit, step=1.0,key="long_limit")
        # Stop limit input box
        long_stop_limit = st.number_input("Stop Limit Price", value=st.session_state.long_stop_limit, step=1.0,key="long_stop_limit")
        refresh_order_data = st.button('Refresh Order Data', on_click=refresh_values, args=(long_amount,long_multiplier,long_order_type,long_limit,long_stop_limit, ),use_container_width=True,key="refresh_long_values")
        with st.form(key='long_trade'):
            st.subheader("Long Trade Data")
            long_price_percent_diff = ((long_limit/get_current_asset_price()['usd'])-1)*100
            if (long_amount == 0.0) and (long_multiplier > 0.0):
                long_amount = long_multiplier*(get_accessible_margin(wallet_address)['readable_amount'])
            long_pnl_wo_fees = (((long_limit/get_current_asset_price()['usd'])-1)*long_amount)
            long_order_df = pd.DataFrame([{"long_amount":long_amount,"long_multiplier":long_multiplier,"long_order_type":long_order_type,"long_limit":long_limit,"long_stop_limit":long_stop_limit,",long_percent_diff":long_price_percent_diff,"pnl_w/o_fees":long_pnl_wo_fees}])
            st.dataframe(long_order_df)
            long_submitted = st.form_submit_button('Execute Long')

    ############################################
    #Short TRADES
    with tcol2:
        # Amount input
        st.subheader("Short Trade")
        if 'short_amount' not in st.session_state:
            st.session_state.short_amount = 0.0
        if 'short_multiplier' not in st.session_state:
            st.session_state.short_multiplier = 0.0
        if 'short_order_type' not in st.session_state:
            st.session_state.short_order_type = "Buy_Limit_Order"
        if 'short_limit' not in st.session_state:
            st.session_state.short_limit = get_current_asset_price()['usd']
        if 'short_stop_limit' not in st.session_state:
            st.session_state.short_stop_limit = get_current_asset_price()['usd']*(1.04)
        
        def refresh_values(short_amount,short_multiplier,short_order_type,short_limit,short_stop_limit):
            st.session_state.short_amount = short_amount
            st.session_state.short_multiplier = short_multiplier
            st.session_state.short_order_type = short_order_type
            st.session_state.short_limit = short_limit
            st.session_state.short_stop_limit = short_stop_limit
            
        short_amount = st.number_input("Margin Amount (Leave at 0 to use leverage multiplier)", value=st.session_state.short_amount,min_value=0.0,max_value=get_leveraged_amount(24.7,wallet_address)['max_asset_leverage']/(10**18), step=10.0,key="short_amount")
        # Slider for liquidation multiplier
        short_multiplier = st.number_input("Liquidation Multiplier",value= st.session_state.short_multiplier, step=1.0,key="short_multiplier")
        # Limit order dropdown
        short_order_type = st.selectbox("Order Type", ["Buy_Limit_Order", "Sell_Limit_Order"],key="short_order_type")
        # Amount input for limit order
        short_limit = st.number_input("Limit Price", value=st.session_state.short_limit, step=1.0,key="short_limit")
        # Stop limit input box
        short_stop_limit = st.number_input("Stop Limit Price", value=st.session_state.short_stop_limit, step=1.0,key="short_stop_limit")
        refresh_order_data = st.button('Refresh Order Data', on_click=refresh_values, args=(short_amount,short_multiplier,short_order_type,short_limit,short_stop_limit, ),use_container_width=True,key="refresh_short_values")
        with st.form(key='short_trade'):
            st.subheader("Short Trade Data")
            short_price_percent_diff = ((short_limit/get_current_asset_price()['usd'])-1)*100
            if (short_amount == 0.0) and (short_multiplier > 0.0):
                short_amount = short_multiplier*(get_accessible_margin(wallet_address)['readable_amount'])
            short_pnl_wo_fees = (((short_limit/get_current_asset_price()['usd'])-1)*short_amount)*-1
            short_order_df = pd.DataFrame([{"short_amount":short_amount,"short_multiplier":short_multiplier,"short_order_type":short_order_type,"short_limit":short_limit,"short_stop_limit":short_stop_limit,"short_percent_diff":short_price_percent_diff,"pnl_w/o_fees":short_pnl_wo_fees}])
            st.dataframe(short_order_df)
            short_submitted = st.form_submit_button('Execute Short')

    # Eventually Implement Threading for limit price threads
    # print(threading.active_count())
    # print(threading.enumerate())
    # getPrice_thread = threading.Thread(target=getPrice,)
    # getPrice_thread.daemon = True
    # getPrice_thread.start()
    
    # Get the candles dataframe
    candles_historicals = get_historicals(token)
    candles_df = pd.DataFrame(candles_historicals['data']['candles'])
    # Display the plotly chart on the dashboard
    with st.expander("Plotly Graph - KWENTA API"):
        st.plotly_chart(get_candlestick_plot_simple(candles_df, "Solana"), use_container_width = True)
    components.html(
    """
    <!-- TradingView Widget BEGIN -->
    <div class="tradingview-widget-container">
    <div id="tradingview_746c1"></div>
    <div class="tradingview-widget-copyright"><a href="https://www.tradingview.com/symbols/SOLUSD/?exchange=COINBASE" rel="noopener" target="_blank"><span class="blue-text">Solana chart</span></a> by TradingView</div>
    <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script type="text/javascript">
    new TradingView.widget(
    {
    "width": 1200,
    "height": 700,
    "symbol": "COINBASE:SOLUSD",
    "interval": "30",
    "timezone": "Etc/UTC",
    "theme": "dark",
    "style": "1",
    "locale": "en",
    "toolbar_bg": "#f1f3f6",
    "enable_publishing": false,
    "withdateranges": true,
    "hide_side_toolbar": false,
    "allow_symbol_change": true,
    "studies": [
        "STD;Stochastic_RSI",
        "STD;Supertrend",
        "STD;VWMA"
    ],
    "container_id": "tradingview_746c1"
    }
    );
    </script>
    </div>
    <!-- TradingView Widget END -->
    """,
    height=700)
