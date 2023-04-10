# Kwenta Python SDK

Python SDK to interact with Kwenta's Smart Contract Systems.

## CAUTION: TRADING WITH MARGIN CAN RESULT IN LOSS. PLEASE TRADE RESPONSIBLY!

## Installation

The SDK requires the following packages to be installed.

numpy, pandas, plotly, requests, streamlit, web3

```bash
pip install -r requirements.txt
```

## Variables

To run this project, you will need to add the following variables filled in the kwenta_config.py script.

`wallet_address` = Wallet Address to trade with.

`private_key` = Private Key to wallet_address

`provider_rpc` = Use your own provider_rpc if you want to refresh faster.

`telegram_token` = Telegram API Token

`telegram_channel_name` = Telegram Channel name (Keep @ in name) ex: @kwenta_limiter


### Telegram integration Steps:
    1. Search telegram for bot named "@botfarther"
    2. Message the bot with and type "/newbot"
    3. Input Bot Name (This will become channel name.)
    4. Copy API token to telegram_token

## Dashboard Deployment

To run the streamlit dashboard run the following. This is still being built. The Python functions however are fully functional.
```bash
  streamlit run .\kwenta-dashboard.py
```


## Features

- Limit + Stop Limit Orders using Kwenta V2
- Open/Close Orders
- Open Orders with Leverage
- Account Safety Checks in-place for positioning
- Move Margin to and from wallet
- Local Dashboard WIP
