import json
import os

# read abi files
with open(f'{os.path.dirname(os.path.abspath(__file__))}/json/PerpsV2MarketData.json') as json_file:
    PerpsV2MarketData_abi = json.load(json_file)

with open(f'{os.path.dirname(os.path.abspath(__file__))}/json/PerpsV2Market.json') as json_file:
    PerpsV2Market_abi = json.load(json_file)

with open(f'{os.path.dirname(os.path.abspath(__file__))}/json/sUSD.json') as json_file:
    sUSD_abi = json.load(json_file)

# create dictionaries
addresses = {
    "sUSD": {
        10: '0x8c6f28f2f1a3c87f0f938b96d27520d9751ec8d9',
        420: '0xeBaEAAD9236615542844adC5c149F86C36aD1136'
    },
    "PerpsV2MarketData": {
        10: '0x58e6227510F83d3F45B339F2f7A05a699fDEE6D4',
        420: '0xcE2dC389fc8Be231beECED1D900881e38596d7b2',
    },
}

abis = {
    "sUSD": sUSD_abi,
    "PerpsV2Market": PerpsV2Market_abi,
    "PerpsV2MarketData": PerpsV2MarketData_abi
}
