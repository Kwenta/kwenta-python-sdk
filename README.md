# Kwenta Python SDK

Python SDK to interact with Kwenta's smart contracts and Synthetix perps.

## Installation

Install the SDK using pip:

```bash
  pip install kwenta
```

## Development
Create a python virtual environment, activate it and install libraries:

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
pip install -e ./module
```

This method will install the local version of the module in editable mode. You can make changes to the SDK and test them without reinstalling the module.

## Usage

To configure an instance of the Kwenta SDK, you need to specify some parameters. At minimum you need to specify the `network_id` and `provider_rpc` to read data from the contracts. If you specify a `wallet_address` and `private_key` you can also submit transactions or create transaction data using the SDK.:

```python
from kwenta import Kwenta

kwenta = Kwenta(
    network_id=10,
    provider_rpc=YOUR_RPC,
    wallet_address=YOUR_ADDRESS,
    private_key=YOUR_PRIVATE_KEY
)
```

To extend the functionality to query subgraphs, Pyth price services, or message on Telegram, you can specify additional parameters.

### Queries / Subgraphs:
- To fetch perps data specify endpoint `gql_endpoint_perps`: [Optimism-perps subgraph](https://thegraph.com/hosted-service/subgraph/kwenta/optimism-perps)
- To fetch rates specify endpoint `gql_endpoint_perps`: [Optimism-perps subgraph](https://thegraph.com/hosted-service/subgraph/kwenta/optimism-perps)

### Pyth:
- Specify the endpoint of a Pyth price service as `price_service_endpoint`

### Telegram:
1. Search telegram for bot named "@botfarther"
2. Message the bot with and type "/newbot"
3. Input bot name (This will become channel name)
4. Specify API token as `telegram_token`
5. Specify channel name as `telegram_channel_name`

## Features
`kwenta`:
- Fetch market info
- Fetch position info
- Open positions
- Close positions
- Modify open positions
- Transfer margin
- Execute and cancel orders
- Limit and stop limit orders

`kwenta.queries`:
- Fetch historical trades
- Fetch historical positions

`kwenta.pyth`:
- Fetch price update data from Pyth price feed
