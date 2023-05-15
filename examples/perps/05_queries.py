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
    3. Submit an order to a perps market
    4. Check the order status
    5. Check the open position
    """
    # configure an instance of the kwenta sdk
    kwenta = Kwenta(
        provider_rpc=PROVIDER_RPC_URL,  # OP mainnet or OP Goerli testnet
        wallet_address=WALLET_ADDRESS,
        private_key=PRIVATE_KEY,  # optional if you want to sign transactions
        network_id=420  # 420 for OP goerli testnet
    )

    # trades for an account
    trades_for_account = await kwenta.queries.trades_for_account()
    print(
        f'Trades for account {kwenta.wallet_address}:\n {trades_for_account}')

    # trades for a market
    asset = 'ETH'
    trades_for_market = await kwenta.queries.trades_for_market(asset)
    print(f'Trades for market {asset}:\n {trades_for_market}')

    # positions for an account
    positions_for_account = await kwenta.queries.positions_for_account()
    print(
        f'Positions for account {kwenta.wallet_address}:\n {positions_for_account}')

    # all open positions
    positions = await kwenta.queries.positions(open_only=True)
    print(f'Open positions:\n {positions}')


if __name__ == '__main__':
    asyncio.run(main())
