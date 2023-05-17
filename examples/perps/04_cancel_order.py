import os
import asyncio
from kwenta import Kwenta
from dotenv import load_dotenv

load_dotenv()

# get env variables
PROVIDER_RPC_URL = os.environ.get('PROVIDER_RPC_URL')
WALLET_ADDRESS = os.environ.get('WALLET_ADDRESS')
PRIVATE_KEY = os.environ.get('PRIVATE_KEY')


async def main():
    """
    1. Configure an instance of the kwenta sdk
    2. Cancel an order for the specified market
    """
    # configure an instance of the kwenta sdk
    kwenta = Kwenta(
        provider_rpc=PROVIDER_RPC_URL,  # OP mainnet or OP Goerli testnet
        wallet_address=WALLET_ADDRESS,
        private_key=PRIVATE_KEY,  # required if you want to sign transactions
        network_id=420  # 420 for OP goerli testnet
    )

    # choose an asset
    asset = 'ETH'

    # if an order is expired, you can cancel it
    order_cancel = kwenta.cancel_order(asset, execute_now=True)
    print(f'Cancel order tx: {order_cancel}\n')


if __name__ == '__main__':
    asyncio.run(main())
