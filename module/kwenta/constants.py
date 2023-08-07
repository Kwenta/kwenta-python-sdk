DEFAULT_NETWORK_ID = 10
DEFAULT_TRACKING_CODE = (
    "0x4b57454e54410000000000000000000000000000000000000000000000000000"
)
DEFAULT_SLIPPAGE = 2.0

DEFAULT_GQL_ENDPOINT_PERPS = {
    10: "https://api.thegraph.com/subgraphs/name/kwenta/optimism-perps",
    420: "https://api.thegraph.com/subgraphs/name/kwenta/optimism-goerli-perps",
}

DEFAULT_GQL_ENDPOINT_RATES = {
    10: "https://api.thegraph.com/subgraphs/name/kwenta/optimism-latest-rates",
    420: "https://api.thegraph.com/subgraphs/name/kwenta/optimism-goerli-latest-rates",
}

DEFAULT_PRICE_SERVICE_ENDPOINTS = {
    10: "https://xc-mainnet.pyth.network",
    420: "https://xc-testnet.pyth.network",
}

ACCOUNT_COMMANDS = {
    "ACCOUNT_MODIFY_MARGIN": [0, ["int256"]],
    "ACCOUNT_WITHDRAW_ETH": [1, ["uint256"]],
    "PERPS_V2_MODIFY_MARGIN": [2, ["address", "int256"]],
    "PERPS_V2_WITHDRAW_ALL_MARGIN": [3, ["address"]],
    "PERPS_V2_SUBMIT_ATOMIC_ORDER": [4, ["address", "int256", "uint256"]],
    "PERPS_V2_SUBMIT_DELAYED_ORDER": [5, ["address", "int256", "uint256", "uint256"]],
    "PERPS_V2_SUBMIT_OFFCHAIN_DELAYED_ORDER": [6, ["address", "int256", "uint256"]],
    "PERPS_V2_CLOSE_POSITION": [7, ["address", "uint256"]],
    "PERPS_V2_SUBMIT_CLOSE_DELAYED_ORDER": [8, ["address", "uint256", "uint256"]],
    "PERPS_V2_SUBMIT_CLOSE_OFFCHAIN_DELAYED_ORDER": [9, ["address", "uint256"]],
    "PERPS_V2_CANCEL_DELAYED_ORDER": [10, ["address"]],
    "PERPS_V2_CANCEL_OFFCHAIN_DELAYED_ORDER": [11, ["address"]],
    "GELATO_PLACE_CONDITIONAL_ORDER": [
        12,
        [
            "bytes32",
            "int256",
            "int256",
            "uint256",
            "ConditionalOrderTypes",
            "uint128",
            "bool",
        ],
    ],
    "GELATO_CANCEL_CONDITIONAL_ORDER": [13, ["uint256"]],
}
