import sys
import json
import os

# read abi files
with open(f'{os.path.dirname(os.path.abspath(__file__))}/abi/PerpsV2MarketData.json') as json_file:
    PerpsV2MarketData_abi = json.load(json_file)

with open(f'{os.path.dirname(os.path.abspath(__file__))}/abi/PerpsV2Market.json') as json_file:
    PerpsV2Market_abi = json.load(json_file)

with open(f'{os.path.dirname(os.path.abspath(__file__))}/abi/sUSD.json') as json_file:
    sUSD_abi = json.load(json_file)

# create dictionaries
addresses = {
    "sUSD": {
        10: '0x8c6f28f2f1a3c87f0f938b96d27520d9751ec8d9'
    },
    "PerpsV2MarketData": {
        10: '0x340B5d664834113735730Ad4aFb3760219Ad9112',
        420: '0x0D9eFa310a4771c444233B10bfB57e5b991ad529',
    },
}

abis = {
    "sUSD": sUSD_abi,
    "PerpsV2Market": PerpsV2Market_abi,
    "PerpsV2MarketData": PerpsV2MarketData_abi
}