from gql import gql

candles = gql(f"""
    query(
        $last_id: ID!
        $token_symbol: String!
        $min_timestamp: BigInt!
        $max_timestamp: BigInt!
        $period: BigInt!
    ) {{
        candles (
            where: {{
                id_gt: $last_id
                synth: $token_symbol
                timestamp_gt: $min_timestamp
                timestamp_lt: $max_timestamp
                period: $period
            }}
            first: 1000
        ) {{
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
        }}
    }}
""")

trades = gql(f"""
    query(
        $last_id: ID!
        $account: Bytes!
    ) {{
        futuresTrades (
            where: {{
                id_gt: $last_id
                account: $account
            }}
            first: 1000
        ) {{
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
        }}
    }}
""")

positions = gql(f"""
    query(
        $last_id: ID!
        $account: Bytes = null
    ) {{
        futuresPositions (
            where: {{
                id_gt: $last_id
                account: $account
            }}
            first: 1000
        ) {{
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
        }}
    }}
""")

queries = {
    'candles': candles,
    'trades': trades,
    'positions': positions
}
