'''
Order Examples:

#Close Position at Limit
limit_price = 22.20
current_pos = get_current_positions(wallet_address)
current_price = get_current_asset_price()
# Short Limit Example
while current_price['usd'] >= limit_price:
    current_price = get_current_asset_price()
    try:
        close_limit(wallet_address,limit_price,short=True)
        time.sleep(1)
    except:
        print("RPC Limited: Waiting 5 Seconds...")
        time.sleep(5)
        
###################################################################
# Long limit Example
limit_price = 21.84
current_pos = get_current_positions(wallet_address)
current_price = get_current_asset_price()
while current_price['usd'] <= limit_price:
    try:
        close_limit(wallet_address,limit_price,short=False)
        time.sleep(1)
    except:
        print("RPC Limited: Waiting 5 Seconds...")
        time.sleep(5)

###################################################################
# Long limit Example with telegram posting
limit_price = 21.84
current_pos = get_current_positions(wallet_address)
current_price = get_current_asset_price()
while current_price['usd'] <= limit_price:
    try:
        close_limit(wallet_address,limit_price,short=False)
        time.sleep(1)
    except:
        print("RPC Limited: Waiting 5 Seconds...")
        time.sleep(5)
sendMessage(f"Limit Price Hit : {limit_price} | Position Closed")

         
###################################################################       
# Open Short Position
limit_price = 22.12
leverage_multiplier = 15
while open == None:
    try:
        open = open_limit(wallet_address,limit_price,leverage_multiplier=leverage_multiplier,short=True)
        time.sleep(1)
    except:
        print("RPC Limited: Waiting 5 Seconds...")
        time.sleep(5)
        

###################################################################
#Open Long Position
limit_price = 21.2
leverage_multiplier = 10
while open == None:
    try:
        open = open_limit(wallet_address,limit_price,leverage_multiplier=leverage_multiplier,short=False)
        time.sleep(1)
    except:
        print("RPC Limited: Waiting 5 Seconds...")
        time.sleep(5)

###################################################################
'''