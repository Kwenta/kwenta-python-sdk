# Kwenta SDK ATS Example

_Disclaimer_

Use this ATS your own risk. We do not guarantee profits or accuracy of the bot's decisions. Trading in financial markets carries inherent risks, and you are solely responsible for your trading decisions. We are not liable for any losses or damages resulting from the use of our trading bot. Please consult with a qualified financial advisor before making any investment decisions.

#

This is an example of how you can use the Kwenta Python SDK to build automated trading systems based on strategy. This example shows how you can can apply a triplesuper trend strat to any market supported by Kwenta.

## Run ATS

1. Install the Kwenta SDK + Example Requirements (_pandas_ta_ is optional, you can remove it from the script if you don't need it.)

```bash
  pip install kwenta pandas schedule pandas_ta
```

Upgrade Kwenta to 1.0.8 if you have not already.

```bash
pip install kwenta --upgrade
```

2. Configure the _Kwenta_supertrend_bot.py_ script with your params

3. Run ATS

```bash
  python Kwenta_supertrend_bot.py
```

## FAQ

#### I'm Stuck and I want to withdrawal everything from a Market.

Run the following: (This will withdrawal everything from the market and send it back to your EOA Wallet)

```
provider_rpc = "Provider_rpc"
wallet_address = "EOA_WALLET_ADDRESS"
private_key = "PRIVATE_KEY"
account = Kwenta(provider_rpc=provider_rpc, wallet_address=wallet_address, private_key=private_key)
account.withdrawal_margin(market, token_amount=-1, withdrawal_all=True, execute_now=True)
account.transfer_margin(market, -1, withdrawal_all=True, execute_now=True)
```

## Optimizations

There's already more alpha in this example script than I would like to leak, but here are some suggestions to make this stronger.

1. Add Shorts -- Currently script only longs
2. Add more indicators. The Example Strategy is very basic, I included some extras for those who are savvy.
3. Use Pyth for higher resolution pricing. Currently using Chainlink Oracle.
4. Utilize Multiple SM Accounts for double sided trades.
