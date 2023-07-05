import click
from kwenta.kwenta import *
import os
import pickle

@click.group()
def kwenta_cli():
    pass

@click.command()
@click.option('--provider-rpc', required=True, help='The provider RPC URL.')
@click.option('--wallet-address', required=True, help='Your wallet address.')
@click.option('--private-key', help='Your private key (optional).')
@click.option('--network-id', type=int, help='Network ID (optional).')
@click.option('--use-estimate-gas/--no-estimate-gas', default=True, help='Use estimated gas (optional).')
@click.option('--gql-endpoint-perps', help='The GraphQL endpoint for perps (optional).')
@click.option('--gql-endpoint-rates', help='The GraphQL endpoint for rates (optional).')
@click.option('--price-service-endpoint', help='The price service endpoint (optional).')
@click.option('--telegram-token', help='Your Telegram bot token (optional).')
@click.option('--telegram-channel-name', help='Your Telegram channel name (optional).')
@click.option('--state-file', default=os.path.join(os.getcwd(), 'kwenta_state.pickle'), help='File to store the kwenta state (optional).')
@click.pass_context
def configure(ctx, provider_rpc, wallet_address, private_key, network_id, use_estimate_gas, gql_endpoint_perps, gql_endpoint_rates, price_service_endpoint, telegram_token, telegram_channel_name, state_file):
    try:
        kwenta_params = {
            "provider_rpc": provider_rpc,
            "wallet_address": wallet_address,
            "private_key": private_key,
            "network_id": network_id,
            "use_estimate_gas": use_estimate_gas,
            "gql_endpoint_perps": gql_endpoint_perps,
            "gql_endpoint_rates": gql_endpoint_rates,
            "price_service_endpoint": price_service_endpoint,
            "telegram_token": telegram_token,
            "telegram_channel_name": telegram_channel_name
        }
        with open(state_file, 'wb') as f:
            pickle.dump(kwenta_params, f)
        click.echo("Kwenta instance parameters saved to the state file.")
    except Exception as e:
        click.echo(f"Error: {str(e)}")


def load_kwenta_instance(state_file):
    if not os.path.exists(state_file):
        raise Exception("State file not found. Please run the 'kwenta' command to create a new instance.")
    try:
        with open(state_file, 'rb') as f:
            kwenta_params = pickle.load(f)
        kwenta_instance = Kwenta(
            provider_rpc=kwenta_params["provider_rpc"],
            wallet_address=kwenta_params["wallet_address"],
            private_key=kwenta_params["private_key"],
            network_id=kwenta_params["network_id"],
            use_estimate_gas=kwenta_params["use_estimate_gas"],
            gql_endpoint_perps=kwenta_params["gql_endpoint_perps"],
            gql_endpoint_rates=kwenta_params["gql_endpoint_rates"],
            price_service_endpoint=kwenta_params["price_service_endpoint"],
            telegram_token=kwenta_params["telegram_token"],
            telegram_channel_name=kwenta_params["telegram_channel_name"]
        )
        return kwenta_instance
    except Exception as e:
        print(e)

@click.command()
@click.argument('token_symbol', type=str)
@click.pass_context
def get_market_contract(ctx, token_symbol):
    try:
        market_contract = kwenta_instance.get_market_contract(token_symbol.upper())
        click.echo(f"Market contract for {token_symbol.upper()}: {market_contract.address}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")

@click.command()
@click.argument('token_symbol', type=str)
@click.argument('wallet_address', type=str)
@click.pass_context
def check_delayed_orders(ctx, token_symbol, wallet_address):
    try:
        if wallet_address is None:
            wallet_address = kwenta_instance.wallet_address
        delayed_order = kwenta_instance.check_delayed_orders(token_symbol.upper(), wallet_address)
        click.echo(f"Delayed order for {token_symbol.upper()} and wallet {wallet_address}: {delayed_order}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")

@click.command()
@click.argument('token_symbol', type=str)
@click.pass_context
def get_current_asset_price(ctx, token_symbol):
    try:
        asset_price = kwenta_instance.get_current_asset_price(token_symbol.upper())
        click.echo(f"Current asset price for {token_symbol.upper()}: {asset_price}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")

@click.command()
@click.argument('token_symbol', type=str)
@click.option('--wallet-address', help='Your wallet address (optional).')
@click.pass_context
def get_current_position(ctx, token_symbol, wallet_address):
    try:
        if wallet_address is None:
            wallet_address = kwenta_instance.wallet_address
        position = kwenta_instance.get_current_position(token_symbol.upper(), wallet_address)
        click.echo(f"Current position for {token_symbol.upper()} and wallet {wallet_address}: {position}")
    except Exception as e:
        click.echo(f"Error1: {str(e)}")

@click.command()
@click.argument('token_symbol', type=str)
@click.pass_context
def get_accessible_margin(ctx, address):
    try:
        result = kwenta_instance.get_accessible_margin(address)
        click.echo(f"Accessible margin for {address}: {result}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")

@click.command()
@click.argument('token_symbol', type=str)
@click.option('--wallet-address', help='The wallet address to check (optional).')
@click.pass_context
def can_liquidate(ctx, token_symbol, wallet_address):
    try:
        result = kwenta_instance.can_liquidate(token_symbol.upper(), wallet_address)
        click.echo(f"Can liquidate {token_symbol.upper()} for wallet {wallet_address}: {result}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")

@click.command()
@click.argument('token_symbol', type=str)
@click.option('--wallet-address', help='The wallet address to liquidate (optional).')
@click.option('--skip-check', is_flag=True, help='Skip liquidation check.')
@click.option('--execute-now', is_flag=True, help='Execute the liquidation now.')
@click.pass_context
def liquidate_position(ctx, token_symbol, wallet_address, skip_check, execute_now):
    try:
        result = kwenta_instance.liquidate_position(token_symbol.upper(), wallet_address, skip_check, execute_now)
        click.echo(f"Liquidation result for {token_symbol.upper()} and wallet {wallet_address}: {result}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")

@click.command()
@click.argument('token_symbol', type=str)
@click.option('--wallet-address', help='The wallet address to flag for liquidation (optional).')
@click.option('--skip-check', is_flag=True, help='Skip liquidation check.')
@click.option('--execute-now', is_flag=True, help='Execute the flag now.')
@click.pass_context
def flag_position(ctx, token_symbol, wallet_address, skip_check, execute_now):
    try:
        result = kwenta_instance.flag_position(token_symbol.upper(), wallet_address, skip_check, execute_now)
        click.echo(f"Flag position result for {token_symbol.upper()} and wallet {wallet_address}: {result}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")

@click.command()
@click.argument('token_symbol', type=str)
@click.pass_context
def get_market_skew(ctx, token_symbol):
    try:
        result = kwenta_instance.get_market_skew(token_symbol.upper())
        click.echo(f"Market skew for {token_symbol.upper()}: {result}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")

@click.command()
@click.pass_context
def get_susd_balance(ctx,wallet_address):
    try:
        result = kwenta_instance.get_susd_balance(wallet_address)
        click.echo(f"sUSD balance: {result}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")


@click.command()
@click.argument("token_symbol", type=str)
@click.argument("leverage_multiplier", type=float)
@click.pass_context
def get_leveraged_amount(ctx, token_symbol, leverage_multiplier):
    try:
        result = kwenta_instance.get_leveraged_amount(token_symbol.upper(), Decimal(leverage_multiplier))
        click.echo(f"Leveraged amount for {token_symbol.upper()}: {result['leveraged_amount']}")
        click.echo(f"Max asset leverage for {token_symbol.upper()}: {result['max_asset_leverage']}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")

@click.command()
@click.argument("token_symbol", type=str)
@click.argument("token_amount", type=int)
@click.option("--execute_now", is_flag=True)
@click.pass_context
def transfer_margin(ctx, token_symbol, token_amount, skip_approval:bool =False,execute_now:bool =False,withdrawal_all:bool =False):
    try:
        result = kwenta_instance.transfer_margin(token_symbol.upper(), token_amount, execute_now=execute_now,withdrawal_all=withdrawal_all)
        if execute_now:
            click.echo(f"Token transfer Tx id: {result}")
        else:
            click.echo(f"Token transfer data: {result}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")

@click.command()
@click.argument("token_symbol", type=str)
@click.argument("size_delta", type=float)
@click.option("--slippage", type=float, default=DEFAULT_SLIPPAGE)
@click.option("--execute_now", is_flag=True)
@click.option("--self_execute", is_flag=True)
@click.pass_context
def modify_position(ctx, token_symbol, size_delta, slippage,wallet_address, execute_now:bool = False, self_execute:bool = False):
    try:
        result = kwenta_instance.modify_position(token_symbol.upper(), size_delta, slippage, wallet_address,execute_now, self_execute)
        if execute_now:
            click.echo(f"Modify position Tx id: {result}")
        else:
            click.echo(f"Modify position data: {result}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")

@click.command()
@click.argument("token_symbol", type=str)
@click.option("--slippage", type=float, default=DEFAULT_SLIPPAGE)
@click.option("--execute_now", is_flag=True)
@click.option("--self_execute", is_flag=True)
@click.pass_context
def close_position(ctx, token_symbol, slippage, wallet_address, execute_now, self_execute):
    try:
        result = kwenta_instance.close_position(token_symbol.upper(), slippage,wallet_address, execute_now, self_execute)
        if execute_now:
            click.echo(f"Close position Tx id: {result}")
        else:
            click.echo(f"Close position data: {result}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")

@click.command()
@click.argument("token_symbol", type=str)
@click.option("--short", is_flag=True)
@click.option("--size_delta", type=float)
@click.option("--slippage", type=float, default=DEFAULT_SLIPPAGE)
@click.option("--leverage_multiplier", type=float)
@click.option("--execute_now", is_flag=True)
@click.option("--self_execute", is_flag=True)
@click.pass_context
def open_position(ctx, token_symbol,wallet_address, short:bool = False, position_size:float =None, slippage:float = 2, leverage_multiplier:float=None, execute_now:bool = False, self_execute:bool = False):
    try:
        result = kwenta_instance.open_position(token_symbol.upper(),wallet_address, short=short, position_size=position_size, slippage=slippage, leverage_multiplier=leverage_multiplier, execute_now=execute_now, self_execute=self_execute)
        if execute_now:
            click.echo(f"Open position Tx id: {result}")
        else:
            click.echo(f"Open position data: {result}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")

@click.command()
@click.argument("order_id", type=int)
@click.option("--execute_now", is_flag=True)
@click.pass_context
def cancel_order(ctx, token_symbol, account,execute_now: bool = False):
    try:
        result = kwenta_instance.cancel_order(token_symbol, account,execute_now=execute_now)
        if execute_now:
            click.echo(f"Cancel order Tx id: {result}")
        else:
            click.echo(f"Cancel order data: {result}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")

@click.command()
@click.argument("sm_accounts", type=int)
@click.pass_context
def sm_accounts(ctx, wallet_address):
    try:
        if wallet_address is None:
            wallet_address = kwenta_instance.wallet_address
        accounts = kwenta_instance.get_sm_accounts()
        click.echo(f"SM Accounts: {accounts}")
    except Exception as e:
        click.echo(f"Error1: {str(e)}")

@click.command()
@click.argument("create_sm_account", type=int)
@click.pass_context
def sm_accounts(ctx, wallet_address,execute_now: bool = False):
    try:
        if wallet_address is None:
            wallet_address = kwenta_instance.wallet_address
        accounts = kwenta_instance.new_sm_account(wallet_address,execute_now=execute_now)
        click.echo(f"Creating new SM Account: {accounts}")
        sm_accounts = kwenta_instance.get_sm_accounts()
        click.echo(f"SM Accounts: {sm_accounts[-1]}")
    except Exception as e:
        click.echo(f"Error1: {str(e)}")



kwenta_cli.add_command(configure)
kwenta_cli.add_command(get_market_contract)
kwenta_cli.add_command(check_delayed_orders)
kwenta_cli.add_command(get_current_asset_price)
kwenta_cli.add_command(get_current_position)
kwenta_cli.add_command(get_accessible_margin)
kwenta_cli.add_command(can_liquidate)
kwenta_cli.add_command(liquidate_position)
kwenta_cli.add_command(flag_position)
kwenta_cli.add_command(get_market_skew)
kwenta_cli.add_command(get_susd_balance)
kwenta_cli.add_command(get_leveraged_amount)
kwenta_cli.add_command(transfer_margin)
kwenta_cli.add_command(modify_position)
kwenta_cli.add_command(close_position)
kwenta_cli.add_command(open_position)
kwenta_cli.add_command(cancel_order)
kwenta_cli.add_command(sm_accounts)

if __name__ == '__main__':
    try:
        state_file = os.path.join(os.getcwd(), 'kwenta_state.pickle')
        kwenta_instance = load_kwenta_instance(state_file)
        click.echo("Kwenta instance loaded from the state file.")
    except Exception as e:
        click.echo(f"State File Location: {str(state_file)}")
        click.echo(f"Error: {str(e)}")
    kwenta_cli()

# Run the "kwenta" command first to create a statefile in the current working directory. All other commands will draw from the statefile 
# python kwenta_cli.py kwenta --provider-rpc 'https://optimism-mainnet.blastapi.io/' --wallet-address "ABC123"
# python kwenta_cli.py get-current-asset-price "SOL"


