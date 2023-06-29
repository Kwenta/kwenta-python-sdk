# Kwenta Python SDK

Python SDK to interact with Kwenta's smart contracts, subgraphs, and Synthetix perps.

## Installation

Install the SDK using pip:

```bash
  pip install kwenta
```

For more information on usage, see the [Usage](#usage) section and the sample scripts.

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

Queries will default to Kwenta's public Hosted Service endpoints for The Graph.

- To fetch perps data specify endpoint `gql_endpoint_perps`: defaults to [Optimism-perps subgraph](https://thegraph.com/hosted-service/subgraph/kwenta/optimism-perps)
- To fetch rates specify endpoint `gql_endpoint_perps`: defaults to [Optimism-perps subgraph](https://thegraph.com/hosted-service/subgraph/kwenta/optimism-perps)

### Pyth:

- Specify the endpoint of a Pyth price service as `price_service_endpoint` defaults to the public Pyth price service. This should be updated for any production applications to use a private Pyth price service.

### Telegram:

1. Search telegram for bot named "@botfather"
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

## SDK Functions

###

```http
  account = Kwenta(INIT VARS)
```

*provider_rpc: (str, required) Endpoint for the provider's RPC.
*wallet_address: (str, required) Wallet address for transactions.
*sm_address: (str, optional) Address of the smart contract, defaults to None.
*private_key: (str, optional) Private key for the wallet, defaults to None.
*network_id: (int, optional) Network ID to connect to, defaults to None.
*use_estimate_gas: (bool, optional) Whether or not to use gas estimation for transactions, defaults to True.
*gql_endpoint_perps: (str, optional) GraphQL endpoint for perps, defaults to None.
*gql_endpoint_rates: (str, optional) GraphQL endpoint for rates, defaults to None.
*price_service_endpoint: (str, optional) Endpoint for the price service, defaults to None.
*telegram_token: (str, optional) Token for the Telegram bot, defaults to None.
\*telegram_channel_name: (str, optional) Name of the Telegram channel for notifications, defaults to None.
