import asyncio
import time
import warnings
from web3 import Web3
from web3.types import TxParams
from web3.middleware import geth_poa_middleware
from decimal import Decimal
from .constants import (
    DEFAULT_NETWORK_ID,
    DEFAULT_TRACKING_CODE,
    DEFAULT_SLIPPAGE,
    DEFAULT_GQL_ENDPOINT_PERPS,
    DEFAULT_GQL_ENDPOINT_RATES,
    DEFAULT_PRICE_SERVICE_ENDPOINTS,
    ACCOUNT_COMMANDS
)
from .contracts import abis, addresses
from .alerts import Alerts
from .queries import Queries
from .pyth import Pyth
from eth_abi import encode
import concurrent.futures

warnings.filterwarnings("ignore")


class Kwenta:
    def __init__(
        self,
        provider_rpc: str,
        wallet_address: str,
        sm_address: str = None,
        private_key: str = None,
        network_id: int = None,
        use_estimate_gas: bool = True,
        gql_endpoint_perps: str = None,
        gql_endpoint_rates: str = None,
        price_service_endpoint: str = None,
        telegram_token: str = None,
        telegram_channel_name: str = None,
        fast_marketload:    bool= False,
    ):
        # set default values
        if network_id is None:
            network_id = DEFAULT_NETWORK_ID

        # init account variables
        self.private_key = private_key
        self.wallet_address = wallet_address
        self.use_estimate_gas = use_estimate_gas
        self.provider_rpc = provider_rpc
        self.fast_marketload = fast_marketload
        # init provider
        if provider_rpc.startswith("https"):
            self.provider_class = Web3.HTTPProvider
        elif provider_rpc.startswith("wss"):
            self.provider_class = Web3.WebsocketProvider
        else:
            raise Exception("RPC endpoint is invalid")

        self.network_id = network_id

        # init contracts
        (
            self.markets,
            self.market_contracts,
            self.susd_token,
            self.sm_account,
        ) = self._load_markets()
        if sm_address is not None:
            self.sm_account = sm_address
        self.token_list = list(self.markets.keys())

        # init alerts
        if telegram_token and telegram_channel_name:
            self.alerts = Alerts(telegram_token, telegram_channel_name)

        # init queries
        if not gql_endpoint_perps:
            gql_endpoint_perps = DEFAULT_GQL_ENDPOINT_PERPS[self.network_id]

        if not gql_endpoint_rates:
            gql_endpoint_rates = DEFAULT_GQL_ENDPOINT_RATES[self.network_id]

        self.queries = Queries(
            self,
            gql_endpoint_perps=gql_endpoint_perps,
            gql_endpoint_rates=gql_endpoint_rates,
        )

        # init pyth
        if not price_service_endpoint:
            price_service_endpoint = DEFAULT_PRICE_SERVICE_ENDPOINTS[self.network_id]

        self.pyth = Pyth(self.network_id, price_service_endpoint=price_service_endpoint)
        self.account_commands = ACCOUNT_COMMANDS

    @property
    def web3(self):
        w3 = Web3(self.provider_class(self.provider_rpc))

        if w3.eth.chain_id != self.network_id:
            raise Exception("The RPC `chain_id` must match the stored `network_id`")
        else:
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            # self.nonce = w3.eth.get_transaction_count(self.wallet_address)
            return w3

    def _load_market(self, market):
        markertsettings_contract = self.web3.eth.contract(
            self.web3.to_checksum_address(
                addresses["PerpsV2MarketSettings"][self.network_id]
            ),
            abi=abis["PerpsV2MarketSettings"],
        )
        maxFundingVelocity = markertsettings_contract.functions.maxFundingVelocity(market[2]).call()
        skewScale = markertsettings_contract.functions.skewScale(market[2]).call()
        normalized_market = {
                "market_address": market[0],
                "asset": market[1].decode("utf-8").strip("\x00"),
                "key": market[2],
                "maxLeverage": market[3],
                "price": market[4],
                "marketSize": market[5],
                "marketSkew": market[6],
                "marketDebt": market[7],
                "currentFundingRate": market[8],
                "currentFundingVelocity": market[9],
                "takerFee": market[10][0],
                "makerFee": market[10][1],
                "takerFeeDelayedOrder": market[10][2],
                "makerFeeDelayedOrder": market[10][3],
                "takerFeeOffchainDelayedOrder": market[10][4],
                "makerFeeOffchainDelayedOrder": market[10][5],
                "maxFundingVelocity": maxFundingVelocity,
                "skewScale": skewScale
            }
        token_symbol = market[2].decode("utf-8").strip("\x00")[1:-4]
        market_contract = self.web3.eth.contract(
            self.web3.to_checksum_address(normalized_market["market_address"]),
            abi=abis["PerpsV2Market"],
        )
        return token_symbol, normalized_market, market_contract

    def _load_markets(self):
        """
        Initializes all market contracts
        ...

        Attributes
        ----------
        N/A
        """
        marketdata_contract = self.web3.eth.contract(
            self.web3.to_checksum_address(
                addresses["PerpsV2MarketData"][self.network_id]
            ),
            abi=abis["PerpsV2MarketData"],
        )
        allmarketsdata = (
            marketdata_contract.functions.allProxiedMarketSummaries().call()
        )
        markets = {}
        market_contracts = {}
        if self.fast_marketload:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = list(executor.map(self._load_market, allmarketsdata))
            for token_symbol, normalized_market, market_contract in results:
                markets[token_symbol] = normalized_market
                market_contracts[token_symbol] = market_contract
        else:
            for market in allmarketsdata:
                normalized_market = {
                    "market_address": market[0],
                    "asset": market[1].decode("utf-8").strip("\x00"),
                    "key": market[2],
                    "maxLeverage": market[3],
                    "price": market[4],
                    "marketSize": market[5],
                    "marketSkew": market[6],
                    "marketDebt": market[7],
                    "currentFundingRate": market[8],
                    "currentFundingVelocity": market[9],
                    "takerFee": market[10][0],
                    "makerFee": market[10][1],
                    "takerFeeDelayedOrder": market[10][2],
                    "makerFeeDelayedOrder": market[10][3],
                    "takerFeeOffchainDelayedOrder": market[10][4],
                    "makerFeeOffchainDelayedOrder": market[10][5],
                }
                token_symbol = market[2].decode("utf-8").strip("\x00")[1:-4]
                markets[token_symbol] = normalized_market
                market_contracts[token_symbol] = self.web3.eth.contract(
                    self.web3.to_checksum_address(normalized_market["market_address"]),
                    abi=abis["PerpsV2Market"],
                )    

        # load sUSD contract
        susd_token = self.web3.eth.contract(
            self.web3.to_checksum_address(addresses["sUSD"][self.network_id]),
            abi=abis["sUSD"],
        )

        sm_account = self.get_sm_accounts()[0]

        return markets, market_contracts, susd_token, sm_account

    def _get_tx_params(self, value=0, to=None) -> TxParams:
        """
        Get the default tx params
        ...

        Attributes
        ----------
        value : int
            value to send in wei
        to : str
            address to send to

        Returns
        -------
        params : dict
            transaction parameters to be completed with another function
        """

        params: TxParams = {
            "from": self.wallet_address,
            "to": to,
            "chainId": self.network_id,
            "value": value,
            "gasPrice": self.web3.eth.gas_price,
            "nonce": self.web3.eth.get_transaction_count(self.wallet_address),
        }
        return params

    def get_market_contract(self, token_symbol: str):
        """
        Run checks and return market contract if it exists
        ...

        Attributes
        ----------
        token_symbol : str
            token symbol from list of supported asset
        """
        if not (token_symbol in self.token_list):
            raise Exception("Token Not in Supported Token List.")
        else:
            return self.market_contracts[token_symbol.upper()]

    def execute_transaction(self, tx_data: dict):
        """
        Execute a transaction given the TX data
        ...

        Attributes
        ----------
        tx_data : dict
            tx data to send transaction
        private_key : str
            private key of wallet sending transaction
        """
        if self.private_key is None:
            raise Exception("No private key specified.")

        if "gas" not in tx_data:
            if self.use_estimate_gas:
                tx_data["gas"] = int(self.web3.eth.estimate_gas(tx_data) * 1.2)
            else:
                tx_data["gas"] = 1500000

        signed_txn = self.web3.eth.account.sign_transaction(
            tx_data, private_key=self.private_key
        )
        tx_token = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        # increase nonce -- getting directly from wallet
        # self.nonce += 1
        return self.web3.to_hex(tx_token)

    def check_delayed_orders(self, token_symbol: str, sm_address: str = None) -> dict:
        """
        Check if delayed order is in queue
        ...

        Attributes
        ----------
        token_symbol : str
            token symbol from list of supported asset
        sm_address : str
            wallet address to check for delayed order
        """
        if not sm_address:
            sm_address = self.sm_account
        market_contract = self.market_contracts[token_symbol]
        delayed_order = market_contract.functions.delayedOrders(sm_address).call()

        return {
            "is_open": True if delayed_order[2] > 0 else False,
            "position_size": delayed_order[1],
            "desired_fill_price": delayed_order[2],
            "intention_time": int(delayed_order[7]),
            "executable_time": int(delayed_order[7]) + 15
            if int(delayed_order[7]) > 0
            else 0,
        }

    def get_sm_accounts(self, wallet_address: str = None) -> dict:
        """
        Gets all the smartmargin accounts for the wallet
        ...

        Attributes
        ----------
        wallet_address : str
        """
        if not wallet_address:
            wallet_address = self.wallet_address
        exch_contract = self.web3.eth.contract(
            self.web3.to_checksum_address(addresses["SMFactory"][self.network_id]),
            abi=abis["SMFactory"],
        )
        sm_accounts = exch_contract.functions.getAccountsOwnedBy(wallet_address).call()
        return sm_accounts

    def new_sm_account(
        self, wallet_address: str = None, execute_now: bool = False
    ) -> dict:
        """
        Creates new smart margin account
        ...

        Attributes
        ----------
        token_symbol : str
            token symbol from list of supported asset
        wallet_address : str
            wallet address to check for delayed order
        """
        if not wallet_address:
            wallet_address = self.wallet_address
        exch_contract = self.web3.eth.contract(
            self.web3.to_checksum_address(addresses["SMFactory"][self.network_id]),
            abi=abis["SMFactory"],
        )
        # new_account = (exch_contract.functions.newAccount().call())
        data_tx = data_tx = exch_contract.encodeABI(fn_name="newAccount", args=[])
        tx_params = self._get_tx_params(
            to=self.web3.to_checksum_address(addresses["SMFactory"][self.network_id])
        )
        tx_params["data"] = data_tx
        # print(tx_params)
        if execute_now:
            tx_token = self.execute_transaction(tx_params)
            print(f"Creating New SM Account")
            print(f"TX: {tx_token}")
            time.sleep(4)
            print(f"SM Accounts: {self.get_sm_accounts()}")
            return tx_token
        else:
            return tx_params

    def get_current_asset_price(self, token_symbol: str) -> dict:
        """
        Gets current asset price for config asset.
        ...

        Attributes
        ----------
        token_symbol : str
            token symbol from list of supported asset

        Returns
        ----------
        Dict with wei and USD price
        """
        market_contract = self.market_contracts[token_symbol.upper()]
        wei_price = (market_contract.functions.assetPrice().call())[0]
        usd_price = self.web3.from_wei(wei_price, "ether")
        return {"usd": usd_price, "wei": wei_price}

    def get_current_position(
        self, token_symbol: str, wallet_address: str = None
    ) -> dict:
        """
        Gets Current Position Data
        ...

        Attributes
        ----------
        token_symbol : str
            token symbol from list of supported asset
        Returns
        ----------
        Dict: position information
        """
        if not wallet_address:
            wallet_address = self.sm_account

        market_contract = self.get_market_contract(token_symbol)
        (
            id,
            last_funding_index,
            margin,
            last_price,
            size,
        ) = market_contract.functions.positions(wallet_address).call()
        current_asset_price = self.get_current_asset_price(token_symbol)

        # clean usd values
        is_short = -1 if size < 0 else 1
        size_ether = self.web3.from_wei(abs(size), "ether") * is_short
        last_price_usd = self.web3.from_wei(last_price, "ether")

        # calculate pnl
        price_diff = current_asset_price["usd"] - last_price_usd
        pnl = size_ether * price_diff * is_short

        positions_data = {
            "id": id,
            "last_funding_index": last_funding_index,
            "margin": margin,
            "last_price": last_price,
            "size": size,
            "pnl_usd": pnl,
        }
        return positions_data

    def get_accessible_margin(self, address: str) -> dict:
        """
        Gets available NON-MARKET account margin
        ...

        Attributes
        ----------
        wallet_address : str
            wallet_address of wallet to check
        token_symbol : str
            token symbol from list of supported asset
        Returns
        ----------
        Dict: Margin remaining in wei and usd
        """
        margin_allowed = self.get_susd_balance(address)["balance"]
        margin_usd = self.web3.from_wei(margin_allowed, "ether")
        return {"margin_remaining": margin_allowed, "margin_remaining_usd": margin_usd}

    def can_liquidate(self, token_symbol: str, wallet_address: str = None) -> dict:
        """
        Checks if Liquidation is possible for wallet
        ...

        Attributes
        ----------
        token_symbol : str
            token symbol from list of supported asset
        Returns
        ----------
        Dict: Liquidation Data
        """
        if not wallet_address:
            wallet_address = self.sm_account
        market_contract = self.get_market_contract(token_symbol)
        liquidation_check = market_contract.functions.canLiquidate(
            wallet_address
        ).call()
        liquidation_price = market_contract.functions.liquidationPrice(
            wallet_address
        ).call()
        return {"liq_possible": liquidation_check, "liq_price": liquidation_price}

    def liquidate_position(
        self,
        token_symbol: str,
        wallet_address: str = None,
        skip_check: bool = False,
        execute_now: bool = False,
    ) -> dict:
        """
        Checks if Liquidation is possible for wallet
        ...

        Attributes
        ----------
        token_symbol : str
            token symbol from list of supported asset
        wallet_address : str
            Wallet address to liquidate
        Returns
        ----------
        Dict: Liquidation of position
        """
        if not wallet_address:
            wallet_address = self.sm_account
        market_contract = self.get_market_contract(token_symbol)
        if skip_check:
            data_tx = market_contract.encodeABI(
                fn_name="liquidatePosition", args=[wallet_address]
            )
            tx_params = self._get_tx_params(to=market_contract.address)
            tx_params["data"] = data_tx
            if execute_now:
                tx_token = self.execute_transaction(tx_params)
                print(f"Executing Liquidation for {token_symbol}")
                print(f"TX: {tx_token}")
                time.sleep(1)
                return tx_token
            else:
                return {"token": token_symbol.upper(), "tx_data": tx_params}
        liquidation_check = market_contract.functions.canLiquidate(
            self.wallet_address
        ).call()
        # check for if liquidation is possible
        if liquidation_check == True:
            data_tx = market_contract.encodeABI(
                fn_name="liquidatePosition", args=[wallet_address]
            )
            tx_params = self._get_tx_params(to=market_contract.address)
            tx_params["data"] = data_tx
            if execute_now:
                tx_token = self.execute_transaction(tx_params)
                print(f"Executing Liquidation for {token_symbol}")
                print(f"TX: {tx_token}")
                time.sleep(1)
                return tx_token
            else:
                return {"token": token_symbol.upper(), "tx_data": tx_params}
        else:
            return {
                "token": token_symbol.upper(),
                "tx_data": "N/A, Cannot Liquidate Position.",
            }

    def flag_position(
        self,
        token_symbol: str,
        wallet_address: str = None,
        skip_check: bool = False,
        execute_now: bool = False,
    ) -> dict:
        """
        Checks if Liquidation is possible for wallet
        ...

        Attributes
        ----------
        token_symbol : str
            token symbol from list of supported asset
        wallet_address : str
            Wallet address to flag for liquidation
        Returns
        ----------
        Dict: flag Liquidation of position
        """
        if not wallet_address:
            wallet_address = self.sm_account
        market_contract = self.get_market_contract(token_symbol)
        if skip_check:
            data_tx = market_contract.encodeABI(
                fn_name="flagPosition", args=[wallet_address]
            )
            tx_params = self._get_tx_params(to=market_contract.address)
            tx_params["data"] = data_tx
            if execute_now:
                tx_token = self.execute_transaction(tx_params)
                print(f"Executing Flag for {token_symbol}")
                print(f"TX: {tx_token}")
                time.sleep(1)
                return tx_token
            else:
                return {"token": token_symbol.upper(), "tx_data": tx_params}
        liquidation_check = market_contract.functions.canLiquidate(
            self.wallet_address
        ).call()
        # check for if liquidation is possible
        if liquidation_check == True:
            data_tx = market_contract.encodeABI(
                fn_name="flagPosition", args=[wallet_address]
            )
            tx_params = self._get_tx_params(to=market_contract.address)
            tx_params["data"] = data_tx
            if execute_now:
                tx_token = self.execute_transaction(tx_params)
                print(f"Executing Flag for {token_symbol}")
                print(f"TX: {tx_token}")
                time.sleep(1)
                return tx_token
            else:
                return {"token": token_symbol.upper(), "tx_data": tx_params}
        else:
            return {
                "token": token_symbol.upper(),
                "tx_data": "N/A, Cannot Flag Position.",
            }

    def get_market_skew(self, token_symbol: str) -> dict:
        """
        Gets current market long/short market skew
        ...

        Attributes
        ----------
        token_symbol : str
            token symbol from list of supported asset

        Returns
        ----------
        Dict with market skew information
        """
        market_contract = self.get_market_contract(token_symbol)
        long, short = market_contract.functions.marketSizes().call()
        total = long + short
        if total == 0:
            percent_long = 0
            percent_short = 0
        else:
            percent_long = long / total * 100
            percent_short = short / total * 100
        return {
            "long": long,
            "short": short,
            "percent_long": percent_long,
            "percent_short": percent_short,
        }
    def get_funding_rate(self, token_symbol:str) -> dict:
        """
        Gets current funding rate for market
        ...
        Attributes
        ----------
        token_symbol : str
            token symbol from list of supported assets
        Returns
        ----------
        Dict with funding information
        """
        market_contract = self.get_market_contract(token_symbol.upper())
        funding_rate = market_contract.functions.currentFundingRate().call()
        if funding_rate < 0:
            rate_percent = self.web3.from_wei(abs(funding_rate),"ether")*-1
        else:
            rate_percent = self.web3.from_wei(abs(funding_rate),"ether")
        return {
            "funding_rate_percent": rate_percent
        }
    def get_funding_velocity(self, token_symbol:str) -> dict:
        """
        Gets current funding rate for market
        ...
        Attributes
        ----------
        token_symbol : str
            token symbol from list of supported assets
        Returns
        ----------
        Dict with funding information
        """
        market_contract = self.get_market_contract(token_symbol.upper())
        funding_rate = market_contract.functions.currentFundingVelocity().call()
        if funding_rate < 0:
            rate_percent = self.web3.from_wei(abs(funding_rate),"ether")*-1
        else:
            rate_percent = self.web3.from_wei(abs(funding_rate),"ether")
        return {
            "funding_velocity_percent": rate_percent
        }
#  getCurrentFundingVelocity ; getCurrentMarketSkew
    def get_susd_balance(self, address: str) -> dict:
        """
        Gets current sUSD Balance in wallet
        ...

        Attributes
        ----------
        wallet_address : str
            wallet_address of wallet to check
        Returns
        ----------
        Dict: wei and usd sUSD balance
        """
        balance = self.susd_token.functions.balanceOf(address).call()
        balance_usd = self.web3.from_wei(balance, "ether")
        return {"balance": balance, "balance_usd": balance_usd}

    def get_leveraged_amount(
        self, token_symbol: str, leverage_multiplier: float, wallet_address: str = None
    ) -> dict:
        """
        Get out amount of leverage available for account
        ...

        Attributes
        ----------
        token_symbol : str
            token symbol from list of supported asset
        leverage_multiplier : int
            leverage multiplier amount. Must be within the range 0.1 - 24.7.

        Returns
        ----------
        Dict: amount of leverage available and max amount of leverage available
        """
        if leverage_multiplier is not None:
            if leverage_multiplier > 24.7 or leverage_multiplier < 0.1:
                print("Leveraged_multiplier must be within the range 0.1 - 24.7!")
                return None
        if wallet_address is None:
            wallet_address = self.sm_account
        margin = (
            self.get_current_position(token_symbol, wallet_address=wallet_address)
        )["margin"]
        asset_price = self.get_current_asset_price(token_symbol)
        # print(f"SUSD Available: {margin}")
        # print(f"Current Asset Price: {asset_price['usd']}")
        # Using 24.7 to cover edge cases
        max_leverage = self.web3.to_wei(
            (margin / asset_price["usd"]) * Decimal(24.7), "ether"
        )
        # print(f"Max Leveraged Asset Amount: {max_leverage}")
        leveraged_amount = (margin / asset_price["wei"]) * leverage_multiplier
        return {
            "leveraged_amount": leveraged_amount,
            "max_asset_leverage": max_leverage,
        }

    def approve_susd(self, susd_amount: int, approve_max: bool = False):
        susd_balance = self.get_susd_balance(self.wallet_address)["balance"]
        if approve_max:
            data_tx = self.susd_token.encodeABI(
                fn_name="approve", args=[self.sm_account, susd_balance]
            )
        else:
            data_tx = self.susd_token.encodeABI(
                fn_name="approve", args=[self.sm_account, susd_amount]
            )
        tx_params = self._get_tx_params(
            to=self.web3.to_checksum_address(addresses["sUSD"][self.network_id])
        )
        tx_params["data"] = data_tx
        tx_params["gas"] = 1500000
        print(f"Approving sUSD: {susd_amount}")
        tx_token = self.execute_transaction(tx_params)
        print(f"TX: {tx_token}")
        return tx_token

    def withdrawal_margin(
        self,
        token_symbol: str,
        token_amount: int = 1,
        withdrawal_all: bool = False,
        execute_now: bool = False,
    ):
        """
        Withdrawal SUSD from Margin Market to Wallet
        ...

        Attributes
        ----------
        token_amount : int
            Token amount *in human readable* to send to Margin account
        token_symbol : str
            token symbol for market
        withdrawal_all: bool
            withdrawal all margin from market
        Returns
        ----------
        str: token transfer Tx id
        """
        sm_account_contract = self.web3.eth.contract(
            self.web3.to_checksum_address(self.sm_account), abi=abis["SM_Account"]
        )
        if token_amount == 0:
            raise Exception("token_amount Cannot be 0.")

        current_position = self.get_current_position(
            token_symbol, wallet_address=self.sm_account
        )["margin"]
        print(f"Current Position: {current_position}")
        if token_amount < current_position:
            is_withdrawal = -1
            token_amount = self.web3.to_wei(abs(token_amount), "ether") * is_withdrawal
            if execute_now:
                if token_amount < 0:
                    print(f"Withdrawal sUSD to {token_symbol} Market.")
                    if withdrawal_all:
                        commandBytes = encode(
                            ["address"],
                            [str(self.markets[token_symbol.upper()]["market_address"])],
                        )
                        data_tx = sm_account_contract.encodeABI(
                            fn_name="execute", args=[[3], [commandBytes]]
                        )
                    else:
                        commandBytes = encode(
                            ["address", "int256"],
                            [
                                str(
                                    self.markets[token_symbol.upper()]["market_address"]
                                ),
                                token_amount,
                            ],
                        )
                        data_tx = sm_account_contract.encodeABI(
                            fn_name="execute", args=[[2], [commandBytes]]
                        )
                    tx_params = self._get_tx_params(to=self.sm_account, value=0)
                    tx_params["data"] = data_tx
                    tx_params["nonce"] = self.web3.eth.get_transaction_count(
                        self.wallet_address
                    )
                    tx_token = self.execute_transaction(tx_params)
                    return tx_token
            else:
                return {"token_amount": token_amount / (10**18), "tx_data": tx_params}
        else:
            print(
                f"Token amount must be less than Current Position: {current_position}"
            )

    def transfer_margin(
        self,
        token_symbol: str,
        token_amount: int,
        skip_approval: bool = False,
        withdrawal_all: bool = False,
        execute_now: bool = False,
    ) -> str:
        """
        Transfers SUSD from wallet to Margin account
        ...

        Attributes
        ----------
        token_amount : int
           sUSD Token amount *in human readable* to send to Margin account
        wallet_address : str
            wallet_address of wallet to check
        skip_approval: bool
            skip susd approval if amount is already approved
        Returns
        ----------
        str: token transfer Tx id
        """
        sm_account_contract = self.web3.eth.contract(
            self.web3.to_checksum_address(self.sm_account), abi=abis["SM_Account"]
        )
        if token_amount == 0:
            raise Exception("token_amount Cannot be 0.")
        #Check for withdrawal 
        is_withdrawal = -1 if token_amount < 0 else 1
        token_amount = self.web3.to_wei(abs(token_amount), "ether") * is_withdrawal
        print(token_amount)
        if is_withdrawal > 0:
            susd_balance = self.get_susd_balance(self.wallet_address)
        else:
            susd_balance = self.get_susd_balance(self.sm_account)
        print(f"sUSD Balance: {susd_balance['balance_usd']}")
        #check that withdrawal is less than account balance
        if (token_amount > susd_balance["balance"]):
            raise Exception(f"Token amount: {token_amount} is greater than Account Balance: {{susd_balance['balance_usd']}}! Verify your balance.")
        #Move amount from EOA Wallet to SM Account 
        if (is_withdrawal > 0):
            if (token_amount > 0) and (skip_approval is False):
                self.approve_susd(token_amount)
                print("Waiting for Approval...")
                time.sleep(4.5)
            #adding to sm account
            if token_amount > 0:
                print(f"Adding sUSD to {token_symbol} Market.")
                time.sleep(4.5)
                print(
                    f"Market_address: {(self.markets[token_symbol.upper()]['market_address'])}"
                )
                commandBytes1 = encode(["int256"], [token_amount])
                commandBytes2 = encode(
                    ["address", "int256"],
                    [
                        str(self.markets[token_symbol.upper()]["market_address"]),
                        token_amount,
                    ],
                )
                data_tx = sm_account_contract.encodeABI(
                    fn_name="execute", args=[[0, 2], [commandBytes1, commandBytes2]]
                )
                tx_params = self._get_tx_params(to=self.sm_account, value=0)
                tx_params["data"] = data_tx
                tx_params["nonce"] = self.web3.eth.get_transaction_count(
                    self.wallet_address
                )
                if execute_now:
                    tx_token = self.execute_transaction(tx_params)
                    print(f"Adding {token_amount} sUSD to Account.")
                    print(f"TX: {tx_token}")
                    return tx_token
                else:
                    return {
                        "token_amount": token_amount / (10**18),
                        "susd_balance": susd_balance,
                        "tx_data": tx_params,
                    }
        #token Amount Negative == Withdrawal to EOA Wallet
        else:
            # Execute Commands: https://github.com/Kwenta/smart-margin/wiki/Commands
            # args[0] == Command ID, args[1] == command inputs, in bytes
            if withdrawal_all:
                token_amount = (int(self.get_accessible_margin(self.sm_account)["margin_remaining"])* -1)
            commandBytes = encode(["int256"], [token_amount])
            data_tx = sm_account_contract.encodeABI(
                fn_name="execute", args=[[0], [commandBytes]]
            )
            tx_params = self._get_tx_params(to=self.sm_account, value=0)
            tx_params["data"] = data_tx
            tx_params["nonce"] = self.web3.eth.get_transaction_count(
                self.wallet_address
            )
            if execute_now:
                tx_token = self.execute_transaction(tx_params)
                print(f"Adding {token_amount} sUSD Moved to EOA Account.")
                print(f"TX: {tx_token}")
                return tx_token
            else:
                return {
                    "token_amount": token_amount / (10**18),
                    "susd_balance": susd_balance,
                    "tx_data": tx_params,
                }
                
    def modify_position(
        self,
        token_symbol: str,
        position_size: float,
        wallet_address: str,
        slippage: float = DEFAULT_SLIPPAGE,
        execute_now: bool = False,
        self_execute: bool = False,
    ) -> str:
        """
        Submits a delayed offchain order with a size of `position_size`
        ...

        Attributes
        ----------
        position_size : float
            Position amount *in human readable* as trade asset i.e. 12 SOL == 12*(10**18). Exact position in a direction, with negative values representing short orders.
        token_symbol : str
            token symbol from list of supported asset
        wallet_address : str
            wallet_address of wallet to check
        slippage : float
            slippage percentage
        self_execute : bool
            If True, wait until the order is executable and execute it

        Returns
        ----------
        str: token transfer Tx id
        """
        sm_account_contract = self.web3.eth.contract(
            self.web3.to_checksum_address(wallet_address), abi=abis["SM_Account"]
        )
        is_short = -1 if position_size < 0 else 1
        position_size = self.web3.to_wei(abs(position_size), "ether") * is_short
        current_position = self.get_current_position(token_symbol)
        current_price = self.get_current_asset_price(token_symbol)
        desired_fill_price = int(
            current_price["wei"] + current_price["wei"] * (slippage / 100) * is_short
        )

        print(f"Current Position Size: {current_position['size']}")
        commandBytes = encode(
            ["address", "int256", "int256"],
            [
                (self.markets[token_symbol.upper()]["market_address"]),
                position_size,
                desired_fill_price,
            ],
        )
        data_tx = sm_account_contract.encodeABI(
            fn_name="execute", args=[[6], [commandBytes]]
        )
        tx_params = self._get_tx_params(to=self.sm_account, value=0)
        tx_params["data"] = data_tx
        print(f"Updating Position by {position_size}")
        if execute_now:
            tx_token = self.execute_transaction(tx_params)
            print(f"TX: {tx_token}")

            if self_execute:
                self._wait_and_execute(tx_token, token_symbol)
            return tx_token
        else:
            return {
                "token": token_symbol.upper(),
                "current_position": current_position["size"],
                "tx_data": tx_params,
            }

    def close_position(
        self,
        token_symbol: str,
        wallet_address: str,
        slippage: float = DEFAULT_SLIPPAGE,
        execute_now: bool = False,
        self_execute: bool = False,
    ) -> str:
        """
        Fully closes account position
        ...

        Attributes
        ----------
        token_symbol : str
            token symbol from list of supported asset
        wallet_address:str
            wallet address -- Should be SM account
        slippage : float
            slippage percentage
        self_execute : bool
            If True, wait until the order is executable and execute it

        Returns
        ----------
        str: token transfer Tx id
        """
        current_position = self.get_current_position(token_symbol)
        current_price = self.get_current_asset_price(token_symbol)
        sm_account_contract = self.web3.eth.contract(
            self.web3.to_checksum_address(wallet_address), abi=abis["SM_Account"]
        )
        is_short = -1 if -current_position["size"] < 0 else 1
        desired_fill_price = int(
            current_price["wei"] + current_price["wei"] * (slippage / 100) * is_short
        )
        print(f"Current Position Size: {current_position['size']}")
        if current_position["size"] == 0:
            print("Not in position!")
            return None
        # Flip position size to the opposite direction
        # Execute Commands: https://github.com/Kwenta/smart-margin/wiki/Commands
        # args[0] == Command ID, args[1] == command inputs, in bytes
        commandBytes = encode(
            ["address", "int256"],
            [
                (self.markets[token_symbol.upper()]["market_address"]),
                desired_fill_price,
            ],
        )
        data_tx = sm_account_contract.encodeABI(
            fn_name="execute", args=[[9], [commandBytes]]
        )
        tx_params = self._get_tx_params(to=self.sm_account, value=0)
        tx_params["data"] = data_tx
        if execute_now:
            tx_token = self.execute_transaction(tx_params)
            print(f"Closing Position by {-current_position['size']}")
            print(f"TX: {tx_token}")
            if self_execute:
                self._wait_and_execute(tx_token, token_symbol)

            return tx_token
        else:
            return {
                "token": token_symbol.upper(),
                "current_position": current_position["size"],
                "tx_data": tx_params,
            }

    def open_position(
        self,
        token_symbol: str,
        wallet_address: str,
        short: bool = False,
        position_size: float = None,
        slippage: float = DEFAULT_SLIPPAGE,
        leverage_multiplier: float = None,
        execute_now: bool = False,
        self_execute: bool = False,
    ) -> str:
        """
        Open account position in a direction
        ...

        Attributes
        ----------
        token_symbol : str
            token symbol from list of supported asset
        wallet_address : str
            Wallet Address to open position in. Should be SM account.
        short : bool, optional
            set to True when creating a short. (Implemented to double check side)
        position_size : int, optional
            position amount in human readable format as trade asset i.e. 12 SOL. Exact position in a direction (Sign this It WILL MATTER).
        leverage_multiplier :
            Multiplier of Leverage to use when creating order. Based on available margin in account.
        slippage : float
            slippage percentage
        self_execute : bool
            If True, wait until the order is executable and execute it

        *Use either position_size or leverage_multiplier.

        Returns
        ----------
        str: token transfer Tx id
        """
        if (position_size is None) and (leverage_multiplier is None):
            print("Enter EITHER a position_size or a leverage_multiplier!")
            return None
        elif (position_size is not None) and (leverage_multiplier is not None):
            print("Enter EITHER a position_size or a leverage_multiplier!")
            return None

        current_position = self.get_current_position(
            token_symbol, wallet_address=wallet_address
        )
        current_price = self.get_current_asset_price(token_symbol)
        sm_account_contract = self.web3.eth.contract(
            self.web3.to_checksum_address(wallet_address), abi=abis["SM_Account"]
        )
        # starting at zero otherwise use Update position
        if current_position["size"] != 0:
            print(f"You are already in a position, use modify_position() instead.")
            print(
                f"Current Position Size: {self.web3.from_wei(current_position['size'], 'ether')}"
            )
            return None
        is_short = -1 if short else 1
        if leverage_multiplier:
            leveraged_amount = self.get_leveraged_amount(
                token_symbol, leverage_multiplier
            )
            max_leverage = leveraged_amount["max_asset_leverage"]
            position_size = leveraged_amount["leveraged_amount"]
            position_size = self.web3.to_wei(abs(position_size), "ether") * is_short
        elif position_size:
            # check side
            if (short == True and position_size > 0) or (
                short == False and position_size < 0
            ):
                print(
                    "Position size and Short value do not line up. Double Check intention."
                )
                return None
            max_leverage = self.get_leveraged_amount(token_symbol, 24.7)[
                "max_asset_leverage"
            ]
            position_size = self.web3.to_wei(abs(position_size), "ether") * is_short
        # checking available margin to make sure this is possible
        if abs(position_size) < max_leverage:
            desired_fill_price = int(
                current_price["wei"]
                + current_price["wei"] * (slippage / 100) * is_short
            )
            # Execute Commands: https://github.com/Kwenta/smart-margin/wiki/Commands
            # args[0] == Command ID, args[1] == command inputs, in bytes
            commandBytes = encode(
                ["address", "int256", "int256"],
                [
                    (self.markets[token_symbol.upper()]["market_address"]),
                    position_size,
                    desired_fill_price,
                ],
            )
            data_tx = sm_account_contract.encodeABI(
                fn_name="execute", args=[[6], [commandBytes]]
            )
            tx_params = self._get_tx_params(to=self.sm_account, value=0)
            tx_params["data"] = data_tx

            if execute_now:
                tx_token = self.execute_transaction(tx_params)
                print(f"Updating Position by {position_size}")
                print(f"TX: {tx_token}")
                if self_execute:
                    self._wait_and_execute(tx_token, token_symbol)
                return tx_token
            else:
                return {
                    "token": token_symbol.upper(),
                    "position_size": position_size / (10**18),
                    "current_position": current_position["size"],
                    "max_leverage": max_leverage / (10**18),
                    "leveraged_percent": (position_size / max_leverage) * 100,
                    "tx_data": tx_params,
                }

    def cancel_order(
        self, token_symbol: str, account: str = None, execute_now: bool = False
    ) -> str:
        """
        Cancels an open order
        ...

        Attributes
        ----------
        account : str
            address of the account to cancel. (defaults to connected wallet)
        token_symbol : str
            token symbol from list of supported asset

        Returns
        ----------
        str: transaction hash for closing the order
        """
        if account is None:
            account = self.sm_account
        delayed_order = self.check_delayed_orders(token_symbol)
        sm_account_contract = self.web3.eth.contract(
            self.web3.to_checksum_address(account), abi=abis["SM_Account"]
        )

        if not delayed_order["is_open"]:
            print("No open order")
            return None

        # Execute Commands: https://github.com/Kwenta/smart-margin/wiki/Commands
        # args[0] == Command ID, args[1] == command inputs, in bytes
        commandBytes = encode(
            ["address"], [(self.markets[token_symbol.upper()]["market_address"])]
        )
        data_tx = sm_account_contract.encodeABI(
            fn_name="execute", args=[[1], [commandBytes]]
        )
        tx_params = self._get_tx_params(to=self.sm_account, value=0)
        tx_params["data"] = data_tx
        if execute_now:
            tx_token = self.execute_transaction(tx_params)
            print(f"Cancelling order for {token_symbol}")
            print(f"TX: {tx_token}")
            return tx_token
        else:
            return {"token": token_symbol.upper(), "tx_data": tx_params}

    def execute_order(
        self,
        token_symbol: str,
        account: str = None,
        execute_now: bool = False,
        estimate_gas: bool = False,
        gas_price: int = None,
        pyth_feed_data: str = None,
    ) -> str:
        """
        Executes an open order
        ...

        Attributes
        ----------
        account : str
            address of the account to execute. (defaults to connected wallet)
        token_symbol : str
            token symbol from list of supported asset

        Returns
        ----------
        str: transaction hash for executing the order
        """
        if not account:
            account = self.wallet_address

        market_contract = self.get_market_contract(token_symbol)
        delayed_order = self.check_delayed_orders(token_symbol, account)

        if not delayed_order["is_open"]:
            print("No open order")
            return None

        if pyth_feed_data is None:
            # get price update data
            pyth_feed_data = self.pyth.price_update_data(token_symbol)

        if not pyth_feed_data:
            raise Exception("Failed to get price update data from price service")

        data_tx = market_contract.encodeABI(
            fn_name="executeOffchainDelayedOrder", args=[account, [pyth_feed_data]]
        )

        tx_params = self._get_tx_params(to=market_contract.address, value=1)
        tx_params["data"] = data_tx

        if execute_now:
            tx_token = self.execute_transaction(tx_params)
            print(f"Executing order for {token_symbol}")
            print(f"TX: {tx_token}")
            return tx_token
        elif gas_price is not None:
            tx_params["gasPrice"] = gas_price
            tx_token = self.execute_transaction(tx_params)
            print(f"Executing order for {token_symbol}")
            print(f"TX: {tx_token}")
            return tx_token
        elif estimate_gas:
            try:
                gas_estimate = self.web3.eth.estimate_gas(tx_params)
                return gas_estimate
            except Exception as e:
                print(f"Error estimating gas: {e}")
                return None
        else:
            return {"token": token_symbol.upper(), "tx_data": tx_params}

    async def _wait_and_execute(self, tx, token_symbol, retries=3, retry_interval=1):
        """
        Wait for a transaction receipt and execute the order when executable
        ...

        Attributes
        ----------
        tx: str
            Transaction hash for the order that was submitted
        token_symbol : str
            token symbol from list of supported asset

        Returns
        ----------
        str: token transfer Tx id
        """
        # wait for receipt
        self.web3.eth.wait_for_transaction_receipt(tx)

        # get delayed order
        delayed_order = self.check_delayed_orders(token_symbol)

        # wait until executable
        print("Waiting until order is executable")
        time.sleep(delayed_order["executable_time"] - time.time())

        # set up the estimate
        gas_estimate = None
        attempt = 0

        # Retry gas estimation multiple times
        while attempt < retries:
            gas_estimate = self.execute_order(token_symbol, estimate_gas=True)

            if gas_estimate is not None:
                break

            print(f"Gas estimation failed, retrying in {retry_interval} seconds...")
            time.sleep(retry_interval)
            attempt += 1

        # If gas estimation is successful, execute the order
        if gas_estimate:
            print(f"Gas estimate for executing order: {gas_estimate}")
            tx_execute = self.execute_order(token_symbol, execute_now=True)
            print(f"Executing tx: {tx_execute}")
        else:
            print(
                "Gas estimation failed after multiple retries, not executing the order."
            )

    async def execute_for_address(
        self, token_symbol, wallet_address, retries=5, retry_interval=1
    ):
        """
        Check an addresses delayed orders and execute the order when executable
        ...

        Attributes
        ----------
        token_symbol : str
            token symbol from list of supported asset
        wallet_address: str
            Transaction hash for the order that was submitted
        """
        if not wallet_address:
            wallet_address = self.wallet_address

        # check delayed orders
        delayed_order = self.check_delayed_orders(token_symbol, wallet_address)

        # if no order, exit
        if not delayed_order["is_open"]:
            print("No delayed order open")
            return

        # wait until executable
        print("Waiting until order is executable")
        await asyncio.sleep(delayed_order["executable_time"] - time.time())

        # set up the estimate
        gas_estimate = None
        attempt = 0

        # Retry gas estimation multiple times
        while attempt < retries:
            gas_estimate = self.execute_order(
                token_symbol, account=wallet_address, estimate_gas=True
            )

            if gas_estimate is not None:
                break

            print(f"Gas estimation failed, retrying in {retry_interval} seconds...")
            await asyncio.sleep(retry_interval)
            attempt += 1

        # If gas estimation is successful, execute the order
        if gas_estimate:
            print(f"Gas estimate for executing order: {gas_estimate}")
            tx_execute = self.execute_order(
                token_symbol, account=wallet_address, execute_now=True
            )
            print(f"Executing tx: {tx_execute}")
        else:
            print(
                "Gas estimation failed after multiple retries, not executing the order."
            )

    def open_limit(
        self,
        token_symbol: str,
        limit_price: float,
        wallet_address: str = None,
        position_size: float = None,
        leverage_multiplier: float = None,
        slippage: float = DEFAULT_SLIPPAGE,
        short: bool = False,
        execute_now: bool = False,
    ) -> str:
        """
        Open Limit position in a direction
        ...

        Attributes
        ----------
        token_symbol : str
            token symbol from list of supported asset
        short : bool, optional
            set to True when creating a short. (Implemented to double check side)
        limit_price : float
            limit price in dollars to open position.
        position_size : int, optional
            position amount in human readable format as trade asset i.e. 12 SOL . Exact position in a direction (Sign this It WILL MATTER).
        leverage_multiplier :
            Multiplier of Leverage to use when creating order. Based on available margin in account.
        slippage : float
            slippage percentage
        *Use either position_size or leverage_multiplier.

        Returns
        ----------
        str: token transfer Tx id
        """
        if wallet_address is None:
            wallet_address = self.sm_account
        if (position_size is None) and (leverage_multiplier is None):
            print("Enter EITHER a position amount or a leverage multiplier!")
            return None
        elif (position_size is not None) and (leverage_multiplier is not None):
            print("Enter EITHER a position amount or a leverage multiplier!")
            return None

        current_position = self.get_current_position(token_symbol)
        current_price = self.get_current_asset_price(token_symbol)

        if current_position["size"] != 0:
            print(f"You are already in a position, use modify_position() instead.")
            print(
                f"Current Position Size: {self.web3.from_wei(current_position['size'], 'ether')}"
            )
            return None

        # Case for position_amount manually set
        if position_size is not None:
            # check Short Position
            if short:
                if current_price["usd"] >= limit_price:
                    return self.open_position(
                        token_symbol,
                        wallet_address,
                        short=True,
                        slippage=slippage,
                        position_size=position_size,
                        execute_now=execute_now,
                    )
            else:
                if current_price["usd"] <= limit_price:
                    return self.open_position(
                        token_symbol,
                        wallet_address,
                        short=False,
                        slippage=slippage,
                        position_size=position_size,
                        execute_now=execute_now,
                    )

        # Case for Leverage Multiplier
        else:
            if short:
                if current_price["usd"] >= limit_price:
                    return self.open_position(
                        token_symbol,
                        wallet_address,
                        short=True,
                        slippage=slippage,
                        leverage_multiplier=leverage_multiplier,
                        execute_now=execute_now,
                    )
            else:
                if current_price["usd"] <= limit_price:
                    return self.open_position(
                        token_symbol,
                        wallet_address,
                        short=False,
                        slippage=slippage,
                        leverage_multiplier=leverage_multiplier,
                        execute_now=execute_now,
                    )
        print(
            f"Limit not reached current : {current_price} | Entry: {current_position['last_price']/(10**18)} | Limit: {limit_price}"
        )
        return None

    def close_limit(
        self,
        token_symbol: str,
        limit_price: float,
        wallet_address: str = None,
        slippage: float = DEFAULT_SLIPPAGE,
        execute_now: bool = False,
    ):
        """
        Close Limit position in a direction
        ...

        Attributes
        ----------
        token_symbol : str
            token symbol from list of supported asset
        limit_price : float
            limit price in *dollars* to open position.
        slippage : float
            slippage percentage
        Returns
        ----------
        str: token transfer Tx id
        """
        if wallet_address is None:
            wallet_address = self.sm_account
        current_position = self.get_current_position(token_symbol)
        current_price = self.get_current_asset_price(token_symbol)

        # Check if you are in Position
        if current_position["size"] == 0:
            print("Not in position!")
            return None

        short = True if current_position["size"] < 0 else False
        if short:
            if current_price["usd"] <= limit_price:
                return self.close_position(
                    token_symbol,
                    wallet_address,
                    slippage=slippage,
                    execute_now=execute_now,
                )
        else:
            if current_price["usd"] >= limit_price:
                return self.close_position(
                    token_symbol,
                    wallet_address,
                    slippage=slippage,
                    execute_now=execute_now,
                )
        print(
            f"Limit not reached current : {current_price['usd']} | Entry: {current_position['last_price']/(10**18)} | Limit: {limit_price}"
        )
        return None

    def close_stop_limit(
        self,
        token_symbol: str,
        limit_price: float,
        stop_price: float,
        wallet_address: str = None,
        slippage: float = DEFAULT_SLIPPAGE,
    ) -> str:
        """
        Close Limit position in a direction with Stop price
        ...

        Attributes
        ----------
        token_symbol : str
            token symbol from list of supported asset
        limit_price : float
            limit price in dollars to open position.
        stop_price : float
            Set to stop price incase of bad position, will exit position if triggered
        slippage : float
            slippage percentage
        Returns
        ----------
        str: token transfer Tx id
        """
        if wallet_address is None:
            wallet_address = self.sm_account
        current_position = self.get_current_position(token_symbol)
        current_price = self.get_current_asset_price(token_symbol)
        # Check if you are in Position
        if current_position["size"] == 0:
            print("Not in position!")
            return None

        short = True if current_position["size"] < 0 else False
        if short:
            if current_price["usd"] <= limit_price:
                return self.close_position(
                    token_symbol, wallet_address, slippage=slippage
                )
            elif current_price["usd"] >= stop_price:
                return self.close_position(
                    token_symbol, wallet_address, slippage=slippage
                )
        else:
            if current_price["usd"] >= limit_price:
                return self.close_position(
                    token_symbol, wallet_address, slippage=slippage
                )
            elif current_price["usd"] <= stop_price:
                return self.close_position(
                    token_symbol, wallet_address, slippage=slippage
                )
        print(
            f"Limit not reached current : {current_price['usd']} | Entry: {current_position['last_price']/(10**18)} | Limit: {limit_price} | Stop Limit: {stop_price}"
        )
        return None

    def execute_chain(
        self, command_list: list, wallet_address: str = None, execute_now: bool = False
    ) -> str:
        """
        Excecute Kwenta Command Chain. Advanced Usage.
        ...
        Attributes
        ----------
        command_list : list
            list of commands to execute with command details
            Example format:
                token_amount = 55000000000
                token_symbol = "SOL"
                command_list = []
                command1_encoded = encode(account.account_commands['ACCOUNT_MODIFY_MARGIN'][1],[token_amount])
                command_list.append([account.account_commands['ACCOUNT_MODIFY_MARGIN'][0],command1_encoded])
                command2_encoded =  encode(account.account_commands['PERPS_V2_MODIFY_MARGIN'][1],[str(account.markets[token_symbol.upper()]["market_address"]),token_amount])
                command_list.append([account.account_commands['PERPS_V2_MODIFY_MARGIN'][0],command2_encoded])
                account.execute_chain(command_list,wallet_address,execute_now=True)
        Returns
        ----------
        str: token transfer Tx id
        """
        
        if wallet_address is None:
            wallet_address = self.sm_account
        sm_account_contract = self.web3.eth.contract(
            self.web3.to_checksum_address(self.sm_account), abi=abis["SM_Account"]
        )
        if execute_now:
            command_ids = []
            command_data = []
            for command in command_list:
                command_ids.append(command[0])
                command_data.append(command[1])
            data_tx = sm_account_contract.encodeABI(
                fn_name="execute", args=[command_ids, command_data]
            )
            tx_params = self._get_tx_params(to=self.sm_account, value=0)
            tx_params["data"] = data_tx
            tx_params["nonce"] = self.web3.eth.get_transaction_count(
                self.wallet_address
            )
            tx_token = self.execute_transaction(tx_params)
            return tx_token
        else:
            return {"command_list": command_list, "tx_data": tx_params}
