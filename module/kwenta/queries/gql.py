from gql import gql
from .config import config

candles = gql("""
    query(
        $last_id: ID!
        $token_symbol: String!
        $min_timestamp: BigInt = 0
        $max_timestamp: BigInt!
        $period: BigInt!
    ) {
        candles (
            where: {
                id_gt: $last_id
                synth: $token_symbol
                timestamp_gt: $min_timestamp
                timestamp_lt: $max_timestamp
                period: $period
            }
            first: 1000
        ) {
            id
            synth
            open
            high
            low
            close
            timestamp
            average
            period
            aggregatedPrices
        }
    }
""")

trades_account = gql("""
    query(
        $last_id: ID!
        $account: Bytes!
        $min_timestamp: BigInt = 0
        $max_timestamp: BigInt!
    ) {
        futuresTrades (
            where: {
                id_gt: $last_id
                account: $account
                timestamp_gt: $min_timestamp
                timestamp_lt: $max_timestamp
            }
            first: 1000
        ) {
			id
			timestamp
			account
			abstractAccount
			accountType
			margin
			size
			marketKey
			asset
			price
			positionId
			positionSize
			positionClosed
			pnl
			feesPaid
			keeperFeesPaid
			orderType
			trackingCode
			fundingAccrued
        }
    }
""")

trades_market = gql("""
    query(
        $last_id: ID!
        $market_key: Bytes!
        $min_timestamp: BigInt = 0
        $max_timestamp: BigInt!
    ) {
        futuresTrades (
            where: {
                id_gt: $last_id
                marketKey: $market_key
                timestamp_gt: $min_timestamp
                timestamp_lt: $max_timestamp
            }
            first: 1000
        ) {
			id
			timestamp
			account
			abstractAccount
			accountType
			margin
			size
			marketKey
			asset
			price
			positionId
			positionSize
			positionClosed
			pnl
			feesPaid
			keeperFeesPaid
			orderType
			trackingCode
			fundingAccrued
        }
    }
""")

positions = gql("""
    query(
        $last_id: ID!
        $is_open: [Boolean!]
    ) {
        futuresPositions (
            where: {
                id_gt: $last_id
                isOpen_in: $is_open
            }
            first: 1000
        ) {
			id
			lastTxHash
			openTimestamp
			closeTimestamp
			timestamp
			market
			marketKey
			asset
			account
			abstractAccount
			accountType
			isOpen
			isLiquidated
			trades
			totalVolume
			size
			initialMargin
			margin
			pnl
			feesPaid
			netFunding
			pnlWithFeesPaid
			netTransfers
			totalDeposits
			fundingIndex
			entryPrice
			avgEntryPrice
			lastPrice
			exitPrice
        }
    }
""")

positions_account = gql("""
    query(
        $last_id: ID!
        $account: Bytes!
        $is_open: [Boolean!]
    ) {
        futuresPositions (
            where: {
                id_gt: $last_id
                account: $account
                isOpen_in: $is_open
            }
            first: 1000
        ) {
			id
			lastTxHash
			openTimestamp
			closeTimestamp
			timestamp
			market
			marketKey
			asset
			account
			abstractAccount
			accountType
			isOpen
			isLiquidated
			trades
			totalVolume
			size
			initialMargin
			margin
			pnl
			feesPaid
			netFunding
			pnlWithFeesPaid
			netTransfers
			totalDeposits
			fundingIndex
			entryPrice
			avgEntryPrice
			lastPrice
			exitPrice
        }
    }
""")

queries = {
    'candles': candles,
    'trades_account': trades_account,
    'trades_market': trades_market,
    'positions': positions,
    'positions_account': positions_account,
}
