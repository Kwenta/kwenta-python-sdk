import os
import asyncio
from kwenta import Kwenta
from dotenv import load_dotenv

load_dotenv()

# get env variables
PROVIDER_RPC_URL = os.environ.get('PROVIDER_RPC_URL')
WALLET_ADDRESS = os.environ.get('WALLET_ADDRESS')
PRIVATE_KEY = os.environ.get('PRIVATE_KEY')


def main():
    """
    1. Configure an instance of the kwenta sdk
    2. Display the sUSD balance of the wallet
    3. Display the available perps markets
    4. Display the market info for each perps market
    """
    # configure an instance of the kwenta sdk
    kwenta = Kwenta(
        provider_rpc=PROVIDER_RPC_URL,  # OP mainnet or OP Goerli testnet
        wallet_address=WALLET_ADDRESS,
        private_key=PRIVATE_KEY,  # required if you want to sign transactions
        network_id=10  # 420 for OP goerli testnet
    )

    # fetch sUSD balance
    balance = kwenta.get_susd_balance()
    print(f'Balance {balance}\n')

    # display the perps markets
    assets = kwenta.markets.keys()
    print(f"Assets: {', '.join(assets)}\n")

    for asset in assets:
        market = kwenta.markets[asset]
        print(f"{asset} Market: {market}\n")


if __name__ == '__main__':
    main()
