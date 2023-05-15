# Examples

This directory contains practical ways to use the `kwenta` library. The examples are organized into folders based on the type of functionality they demonstrate. Each example is a standalone script that can be run from the command line.

Before running any scripts, make sure to install libraries and set any required environment variables as specified in the [main README](../README.md#development).

Folders:
- [**Perps**](./perps): A collection of scripts to onboard new users to functions in the Kwenta SDK
  1. [Configure](./perps/01_configure.py): Configure the SDK with your network and wallet information
  2. [Market info](./perps/02_market_info.py): Fetch market information from the perps contracts
  3. [Make trade](./perps/03_make_trade.py): A simple implementation for transferring margin and opening a position
  4. [Cancel order]((./perps/04_cancel_order.py)): Cancels an open order on a perps market
  5. [Query](./perps/05_queries.py): Query the perps subgraph for trading data
- [**Keeper**](./keeper/order_keeper.py): A simple keeper bot that monitors the perps contract and executed delayed offchain orders on the markets.
