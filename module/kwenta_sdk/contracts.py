import sys
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
		10: '0xF7D3D05cCeEEcC9d77864Da3DdE67Ce9a0215A9D',
		420: '0x0D9eFa310a4771c444233B10bfB57e5b991ad529',
	},
}

abis = {
	"sUSD": sUSD_abi,
	"PerpsV2Market": PerpsV2Market_abi,
	"PerpsV2MarketData": PerpsV2MarketData_abi
}
