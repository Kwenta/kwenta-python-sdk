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
    """
    # configure an instance of the kwenta sdk
    kwenta = Kwenta(
        provider_rpc=PROVIDER_RPC_URL,  # OP mainnet or OP Goerli testnet
        wallet_address=WALLET_ADDRESS,
        private_key=PRIVATE_KEY,  # optional if you want to sign transactions
        network_id=10  # 420 for OP goerli testnet
    )

    # choose an asset
    asset = 'ETH'

    # get the market info for the asset
    market = kwenta.markets[asset]
    print(f'{asset} Market: {market}\n')

    # get the current asset price
    current_asset_price = kwenta.get_current_asset_price(asset)

    # get the market skew
    market_skew = kwenta.get_market_skew(asset)

    # get position for the connected wallet
    current_position = kwenta.get_current_position(asset)

    # get the accessible margin for the connected wallet
    accessible_margin = kwenta.get_accessible_margin(asset)

    # check if there is a delayed order for the connected wallet
    delayed_order = kwenta.check_delayed_orders(asset)

    # check if the connected wallet's position can be liquidated
    can_liquidate = kwenta.can_liquidate(asset)

    # calculated the size of an order with 3x leverage
    # this calculation is based on the current margin and asset price
    # leveraged_amount = (accessible_margin * 3) / current_asset_price
    leveraged_amount = kwenta.get_leveraged_amount(asset, 3)

    print(f'Asset price: {current_asset_price}', '\n')
    print(f'Skew: {market_skew}', '\n')
    print(f'Position: {current_position}', '\n')
    print(f'Margin: {accessible_margin}', '\n')
    print(f'Delayed order: {delayed_order}', '\n')
    print(f'Can liquidate: {can_liquidate}', '\n')
    print(f'Leveraged amount: {leveraged_amount}', '\n')


if __name__ == '__main__':
    main()
