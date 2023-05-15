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
    2. Submit a margin transfer to a perps market
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

    # choose an asset
    asset = 'ETH'

    # get the market info for the asset
    market = kwenta.markets[asset]
    print(f'{asset} Market: {market}\n')

    # check margin balance
    margin_balance_before = kwenta.get_accessible_margin(asset)
    print(f'Starting margin balance: {margin_balance_before}\n')

    # transfer margin to the market
    transfer_margin = kwenta.transfer_margin(asset, 100, execute_now=True)
    print(f'Transfer tx: {transfer_margin}\n')

    # wait for the transfer to be mined
    kwenta.web3.eth.wait_for_transaction_receipt(transfer_margin)
    print('Transfer transaction confirmed\n')
    await asyncio.sleep(10)

    # check margin balance again
    margin_balance_after = kwenta.get_accessible_margin(asset)
    print(f'Ending margin balance: {margin_balance_after}\n')

    # submit an order
    open_position = kwenta.modify_position(
        asset, size_delta=0.5, execute_now=True)
    print(f'Open position tx: {open_position}\n')

    # wait for the transfer to be mined
    kwenta.web3.eth.wait_for_transaction_receipt(open_position)
    print('Order transaction confirmed\n')
    await asyncio.sleep(2)

    # check the order status
    order_before = kwenta.check_delayed_orders(asset)
    print(f'Order before: {order_before}\n')
    await asyncio.sleep(20)

    # check the open position
    position = kwenta.get_current_position(asset)
    print(f'Position: {position}\n')

    # check the order status again
    order_after = kwenta.check_delayed_orders(asset)
    print(f'Order after: {order_after}\n')


if __name__ == '__main__':
    asyncio.run(main())
