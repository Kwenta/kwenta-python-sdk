import os
import asyncio
from kwenta import Kwenta

PROVIDER_RPC_URL = os.environ.get('PROVIDER_RPC_URL')
WALLET_ADDRESS = os.environ.get('WALLET_ADDRESS')
PRIVATE_KEY = os.environ.get('PRIVATE_KEY')
PYTH_PRICE_SERVER = os.environ.get('PYTH_PRICE_SERVICE_URL')


class Keeper:
    def __init__(self):
        self.kwenta = Kwenta(
            provider_rpc=PROVIDER_RPC_URL,
            private_key=PRIVATE_KEY,
            wallet_address=WALLET_ADDRESS,
            price_service_endpoint=PYTH_PRICE_SERVER,
            network_id=10,
        )

    async def process_event(self, event, token_symbol):
        # Extract the required information from the event
        account = event["args"]["account"]
        tracking_code = event["args"]["trackingCode"].decode(
            'utf-8').rstrip('\x00')

        # Call get_delayed_order and wait for the executable time
        if tracking_code == 'KWENTA':
            print(f'executing for {account} for token {token_symbol}')
            await self.kwenta.execute_for_address(token_symbol, account)

    async def monitor_events(self):
        PerpsMarkets = [self.kwenta.get_market_contract(
            token) for token in self.kwenta.token_list]

        event_filters = [PerpsMarket.events.DelayedOrderSubmitted.create_filter(
            fromBlock="latest") for PerpsMarket in PerpsMarkets]

        while True:
            print('getting new events')
            for ind, event_filter in enumerate(event_filters):
                try:
                    events = event_filter.get_new_entries()

                    for event in events:
                        asyncio.create_task(self.process_event(
                            event, self.kwenta.token_list[ind]))
                except Exception as e:
                    print(e)

            await asyncio.sleep(7)  # Adjust the sleep time as needed


async def main():
    keeper = Keeper()
    await keeper.monitor_events()

if __name__ == "__main__":
    asyncio.run(main())
