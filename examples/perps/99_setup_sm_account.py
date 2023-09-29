import os
import time
from dotenv import load_dotenv
from eth_account import Account
from eth_account.signers.local import LocalAccount
from kwenta import Kwenta, contracts
from web3 import Web3
from web3.middleware import construct_sign_and_send_raw_middleware
from web3.types import TxParams

load_dotenv()

# get env variables
PROVIDER_RPC_URL = os.environ.get("PROVIDER_RPC_URL")
WALLET_ADDRESS = os.environ.get("WALLET_ADDRESS")
PRIVATE_KEY = os.environ.get("PRIVATE_KEY")
NETWORK_ID = 10  # 10 for OP mainnet


def setup_sm_account():
    # Setting up the web3 library so we can interact with the OP chain
    web3 = Web3(Web3.HTTPProvider(PROVIDER_RPC_URL, request_kwargs={"timeout": 60}))
    account: LocalAccount = Account.from_key(PRIVATE_KEY)
    web3.middleware_onion.add(construct_sign_and_send_raw_middleware(account))

    # The address of the Kwenta contract that has the function for creating the SM account
    smfactory_address = contracts.addresses["SMFactory"][NETWORK_ID]
    contract = web3.eth.contract(
        web3.to_checksum_address(smfactory_address),
        abi=contracts.abis["SMFactory"],
    )
    data_tx = contract.encodeABI(fn_name="newAccount", args=[])

    # Collecting everything we need to include in the transaction
    tx_params: TxParams = {
        "from": WALLET_ADDRESS,
        "to": smfactory_address,
        "chainId": NETWORK_ID,
        "value": 0,
        "gasPrice": web3.eth.gas_price,
        "nonce": web3.eth.get_transaction_count(WALLET_ADDRESS),
        "data": data_tx,
    }

    # Estimating how much gas this transaction would cost and adding 20% safety margin on top
    tx_params["gas"] = int(web3.eth.estimate_gas(tx_params) * 1.2)

    # And finally signing and submitting the transaction to the network
    signed_txn = web3.eth.account.sign_transaction(tx_params, private_key=PRIVATE_KEY)
    tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    tx_hex_token = web3.to_hex(tx_token)
    print(f"Transaction submitted: https://optimistic.etherscan.io/tx/{tx_hex_token}")

    # Wait for couple block intervals for our transaction to get processed
    time.sleep(4)


def init_kwenta():
    return Kwenta(
        provider_rpc=PROVIDER_RPC_URL,  # OP mainnet or OP Goerli testnet
        wallet_address=WALLET_ADDRESS,
        private_key=PRIVATE_KEY,  # required if you want to sign transactions
        network_id=NETWORK_ID,
    )


def main():
    """
    1. Initialize the Kwenta SDK to check if a SM account is already created
    2. If init fails, create the raw transaction to create an account
    3. Retry to initialize the Kwenta SDK
    4. Get the account balance to confirm you are setup and ready to go
    """
    # Try to initialize the SDK
    # This will fail with an IndexError if no SM account exists for this wallet yet
    try:
        print("Checking if your wallet already has a Smart Margin account...")
        kwenta = init_kwenta()

    # Submit a transaction outside the SDK to set up the account
    except IndexError:
        print("You don't seem to have an account yet. Let's create one...")
        setup_sm_account()
        # Try again to initialize the SDK
        kwenta = init_kwenta()

    # Confirm that SDK is now properly initialized
    balance = kwenta.get_susd_balance(WALLET_ADDRESS)
    print(f"Your account balance: {balance}\n")


if __name__ == "__main__":
    main()
