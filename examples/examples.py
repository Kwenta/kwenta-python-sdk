'''
Order Examples:

#Close Position at Limit
account = kwenta(provider_rpc, wallet_address, private_key)
token_symbol = 'sol'
limit_price = 20.45
current_pos = account.get_current_positions(token_symbol)
current_price = account.get_current_asset_price(token_symbol)
# Short Limit Example
while current_price['usd'] >= limit_price:
    current_price = account.get_current_asset_price(token_symbol)
    try:
        account.close_limit(token_symbol,limit_price,short=True)
        time.sleep(1)
    except Exception as e:
        print(e)
        print("RPC Limited: Waiting 5 Seconds...")
        time.sleep(5)

###################################################################
# Long limit Example
account = kwenta(provider_rpc, wallet_address, private_key)
token_symbol = "SOL"
limit_price = 20.94
current_pos = account.get_current_positions(token_symbol)
current_price = account.get_current_asset_price(token_symbol)
# Short Limit Example
while current_price['usd'] <= limit_price:
    current_price = account.get_current_asset_price(token_symbol)
    try:
        account.close_limit(token_symbol,limit_price,short=False)
        time.sleep(1)
    except:
        print("RPC Limited: Waiting 5 Seconds...")
        time.sleep(5)

###################################################################
# Long limit Example with telegram posting
account = kwenta(provider_rpc, wallet_address, private_key)
token_symbol = 'sol'
limit_price = 20.45
current_pos = account.get_current_positions(token_symbol)
current_price = account.get_current_asset_price(token_symbol)
# Short Limit Example
while current_price['usd'] >= limit_price:
    current_price = account.get_current_asset_price(token_symbol)
    try:
        account.close_limit(token_symbol,limit_price,short=False)
        time.sleep(1)
    except Exception as e:
        print(e)
        print("RPC Limited: Waiting 5 Seconds...")
        time.sleep(5)
sendMessage(f"Limit Price Hit : {limit_price} | Position Closed")


###################################################################

'''
