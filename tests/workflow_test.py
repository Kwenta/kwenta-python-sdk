# Kwenta SDK Workflow test.
# Transfer Margin, Open Position, Close Postion, transfer out margin, withdrawal back to wallet.
# Sleeps are required to ensure execution
from kwenta import Kwenta
from web3 import Web3
from eth_abi import encode
import time

wallet_address = "wallet_address"
private_key = "private_key"
provider_rpc = "provider_rpc"
# initalize web3
account = Kwenta(
    provider_rpc=provider_rpc, wallet_address=wallet_address, private_key=private_key
)
account.get_sm_accounts()
# account.new_sm_account(execute_now=True)
print("Testing Asset Price")
account.get_current_asset_price("SOL")
account.get_current_position("SOL")
smaccount = account.get_sm_accounts()[0]
account.get_susd_balance(smaccount)
account.get_susd_balance(wallet_address)
print("transfer_margin...")
account.transfer_margin("SOL", 55, execute_now=True)
time.sleep(4)
account.get_leveraged_amount("SOL", 5)
print("Testing Limit Order")
account.open_limit(
    "SOL",
    float(account.get_current_asset_price("SOL")["usd"] / 2),
    short=False,
    leverage_multiplier=5,
    execute_now=True,
)
print("open_position...")
account.open_position(
    "SOL", smaccount, short=False, leverage_multiplier=5, execute_now=True
)
time.sleep(10)
account.check_delayed_orders("SOL")
time.sleep(10)
account.get_current_position("SOL", wallet_address=smaccount)
print("close_position...")
account.close_position("SOL", smaccount, execute_now=True)
time.sleep(10)
account.get_current_position("SOL", wallet_address=smaccount)
print("Withdrawal_margin from Market...")
account.withdrawal_margin("SOL", token_amount=1, withdrawal_all=True, execute_now=True)
time.sleep(4)
margin_in_account = int(
    account.get_accessible_margin(smaccount)["margin_remaining_usd"]
)
print("transfer_margin from SM_account...")
# account.transfer_margin("SOL",(margin_in_account*-1),execute_now=True)
account.transfer_margin("SOL", token_amount=-1, withdrawal_all=True, execute_now=True)
time.sleep(4)
account.get_susd_balance(smaccount)
account.get_susd_balance(wallet_address)
