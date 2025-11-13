# =====================
# This is a Sample script that places a Buy order, waits 10 seconds, and then places a Sell order.
# =====================
import random
import string
import time

from growwapi import GrowwAPI

# =====================
# STEP 1: Setup
# =====================

# === Setup Groww API ===
# Please use the "Generate API key" option on the API keys page to obtain the API key and Secret.


user_api_key = "eyJraWQiOiJaTUtjVXciLCJhbGciOiJFUzI1NiJ9.eyJleHAiOjI1NTEwOTcwODksImlhdCI6MTc2MjY5NzA4OSwibmJmIjoxNzYyNjk3MDg5LCJzdWIiOiJ7XCJ0b2tlblJlZklkXCI6XCI0M2FjMGUwYi0zMWU0LTRiODAtYWQxNS0wNGQ5MTk1NWQyNzRcIixcInZlbmRvckludGVncmF0aW9uS2V5XCI6XCJlMzFmZjIzYjA4NmI0MDZjODg3NGIyZjZkODQ5NTMxM1wiLFwidXNlckFjY291bnRJZFwiOlwiMWFhMmJjMTUtMWEwYy00ZWU4LWEyZjUtMmM3MmMxYTRhMjhjXCIsXCJkZXZpY2VJZFwiOlwiOWQyNDA2MjktY2MxZS01MWNiLWFkZGYtMjc3ZjFmZWE0ZDY3XCIsXCJzZXNzaW9uSWRcIjpcIjYzYjllZGE3LWRiMTctNDUzOS05ZTZkLTc5OTg2YWVjMzg2OVwiLFwiYWRkaXRpb25hbERhdGFcIjpcIno1NC9NZzltdjE2WXdmb0gvS0EwYkYxY2pIU251QkY4VzVpamFGR2JXenRSTkczdTlLa2pWZDNoWjU1ZStNZERhWXBOVi9UOUxIRmtQejFFQisybTdRPT1cIixcInJvbGVcIjpcImF1dGgtdG90cFwiLFwic291cmNlSXBBZGRyZXNzXCI6XCIxMTUuOTguMTg5LjM1LDE2Mi4xNTguMjM1LjYyLDM1LjI0MS4yMy4xMjNcIixcInR3b0ZhRXhwaXJ5VHNcIjoyNTUxMDk3MDg5MTg4fSIsImlzcyI6ImFwZXgtYXV0aC1wcm9kLWFwcCJ9.Z5ve6H2WFg2HViKYX_c1PMfv4OHUOBqEFQwil9oyIEbD66k0128h3ddOt2ImbCfl9VJH5EStIwoW8FU5IbRW8g"
user_secret = "$QI-AzB(L^nfI&VvfUyG)!rJwVg#ifOG"


access_token = GrowwAPI.get_access_token(api_key = user_api_key, secret = user_secret)
# Use access_token to initiate GrowwAPi
groww = GrowwAPI(access_token)
print("✅ Ready to Groww")

def setAdjustment(position):
    if(position['optionType']=='PE'):
        for i in range(15):
            currentspot = int(position['spot']) + i*50
            quote_response = groww.get_quote(
                exchange=groww.EXCHANGE_NSE,
                segment=groww.SEGMENT_FNO,
                trading_symbol=position['expiry']+str(currentspot)+position['optionType']
            )
            #print(quote_response)
            random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=9))

            if(quote_response['last_price']-position['net_price'] > 1):
                place_order_response = groww.place_order(
                    trading_symbol=position['expiry']+str(currentspot)+position['optionType'],
                    quantity=position['debit_quantity'],
                    validity=groww.VALIDITY_DAY,
                    exchange=groww.EXCHANGE_NSE,
                    segment=position['segment'],
                    product=groww.PRODUCT_NRML,
                    order_type=groww.ORDER_TYPE_MARKET,
                    transaction_type=groww.TRANSACTION_TYPE_SELL,
                    order_reference_id="Ab-"+random_string+"-1628190"  # Optional: User provided 8 to 20 length alphanumeric reference ID to track the order
                )
                print(place_order_response)
                time.sleep(3)
                return currentspot
            else:
                continue
    else:
        for i in range(15):
            currentspot = int(position['spot']) - i*50
            quote_response = groww.get_quote(
                exchange=groww.EXCHANGE_NSE,
                segment=groww.SEGMENT_FNO,
                trading_symbol=position['expiry']+str(currentspot)+position['optionType']
            )
            #print(quote_response)
            random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=9))

            if(quote_response['last_price']-position['net_price'] > 1):
                place_order_response = groww.place_order(
                    trading_symbol=position['expiry']+str(currentspot)+position['optionType'],
                    quantity=position['debit_quantity'],
                    validity=groww.VALIDITY_DAY,
                    exchange=groww.EXCHANGE_NSE,
                    segment=position['segment'],
                    product=groww.PRODUCT_NRML,
                    order_type=groww.ORDER_TYPE_MARKET,
                    transaction_type=groww.TRANSACTION_TYPE_SELL,
                    order_reference_id="Ab-"+random_string+"-1628190"  # Optional: User provided 8 to 20 length alphanumeric reference ID to track the order
                )
                print(place_order_response)
                time.sleep(3)
                return currentspot
            else:
                continue


def closeposition(position):
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=9))

    place_order_response = groww.place_order(
        trading_symbol=position['trading_symbol'],
        quantity=position['debit_quantity'],
        validity=groww.VALIDITY_DAY,
        exchange=groww.EXCHANGE_NSE,
        segment=position['segment'],
        product=groww.PRODUCT_NRML,
        order_type=groww.ORDER_TYPE_MARKET,
        transaction_type=groww.TRANSACTION_TYPE_BUY,
        order_reference_id="Ab-"+random_string+"-1628190"  # Optional: User provided 8 to 20 length alphanumeric reference ID to track the order
    )
    print(place_order_response)
    time.sleep(3)

    pass


def setHoldings():
    global holdings_response, oneposition, onenet, twoposition, twonet
    holdings_response = groww.get_positions_for_user()
    print("Original Holdings")
    #print(holdings_response)
    for position in holdings_response['positions']:
        print('trading_symbol=',position['trading_symbol'],'quantity',position['quantity'],'net_price',position['net_price'],'realised_pnl',position['realised_pnl'])
    print("-------------------------------------")
    for item in holdings_response['positions'].copy():  # Iterate over a copy
        if item['quantity'] == 0:  # Remove closed/zero numbers
            holdings_response['positions'].remove(item)
    print("Open Holdings")
    #print(holdings_response['positions'])
    for position in holdings_response['positions']:
        print('trading_symbol=',position['trading_symbol'],'quantity',position['quantity'],'net_price',position['net_price'],'realised_pnl',position['realised_pnl'])
    print("-------------------------------------")
    oneposition = holdings_response['positions'][0]
    onenet = holdings_response['positions'][0]['net_price']
    oneSpot = "" + oneposition['trading_symbol'][:-2]
    oneposition['spot'] = oneSpot[len(oneSpot) - 5:len(oneSpot)]
    print("one option spot ", oneposition['spot'])
    oneposition['optionType'] = "" + oneposition['trading_symbol'][-2:]
    oneposition['expiry'] = "" + oneposition['trading_symbol'][:-7]
    print("one option type " ,oneposition['optionType'])
    print("one option expiry " ,oneposition['expiry'])
    print("No of positions ", len(holdings_response['positions']))
    if(len(holdings_response['positions']) > 1):
        twoposition = holdings_response['positions'][1]
        twonet = holdings_response['positions'][1]['net_price']
        twoSpot = "" + twoposition['trading_symbol'][:-2]
        twoposition['spot'] = twoSpot[len(twoSpot) - 5:len(twoSpot)]
        print("two option spot ", twoposition['spot'])
        twoposition['optionType'] = "" + twoposition['trading_symbol'][-2:]
        twoposition['expiry'] = "" + twoposition['trading_symbol'][:-7]
        print("two option type ", twoposition['optionType'])
        print("two option expiry ", twoposition['expiry'])


def placelimitOrder(position,limitValue):
    global length, random_string, place_order_response
    length = 9
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    place_order_response = groww.place_order(
        trading_symbol=position['trading_symbol'],
        quantity=position['debit_quantity'],
        validity=groww.VALIDITY_DAY,
        exchange=groww.EXCHANGE_NSE,
        segment=position['segment'],
        product=groww.PRODUCT_NRML,
        order_type=groww.ORDER_TYPE_LIMIT,
        price=limitValue,
        transaction_type=groww.TRANSACTION_TYPE_BUY,
        order_reference_id="Ab-" + random_string + "-1628190"
        # Optional: User provided 8 to 20 length alphanumeric reference ID to track the order
    )
    print(place_order_response)
    time.sleep(3)


try:

    setHoldings()

    adjustone3x = False
    adjusttwo3x = False
    adjustone2x = False
    adjusttwo2x = False
    one90close = False
    two90close = False

    while len(holdings_response['positions']) >= 2 :
        quote_response = groww.get_quote(
            exchange=groww.EXCHANGE_NSE,
            segment=groww.SEGMENT_FNO,
            trading_symbol=holdings_response['positions'][0]['trading_symbol']
        )
        #print(quote_response['last_price'])

        onelive = quote_response['last_price']

        time.sleep(3)
        quote_response = groww.get_quote(
            exchange=groww.EXCHANGE_NSE,
            segment=groww.SEGMENT_FNO,
            trading_symbol=holdings_response['positions'][1]['trading_symbol']
        )
        #print(quote_response['last_price'])

        twolive = quote_response['last_price']

        if onelive > onenet*3 and adjustone3x == False:
            print(onenet, onelive, "Exiting one as price to 3x ",onenet*3)
            closeposition(oneposition)
            adjustone3x = True
            time.sleep(3)
            setHoldings()
        else:
            print(onenet, onelive,  " skipping one as not thripled ",onenet*3)
            time.sleep(3)

        if twolive > twonet*3 and adjusttwo3x == False:
            print(twonet, twolive, " Exiting two as price to 3x ",twonet*3)
            closeposition(twoposition)
            adjusttwo3x = True
            time.sleep(3)
            setHoldings()

        else:
            print(twonet, twolive, "skipping two as not thripled ",twonet*3)
            time.sleep(3)

        if onelive > onenet*2 and adjustone2x == False:
            print(onenet, onelive," switch second to move forward ",onenet*2)
            closeposition(twoposition)
            setAdjustment(twoposition)
            adjustone2x = True
            setHoldings()

        else:
            print(onenet, onelive,  " skipping one as not doubled ",onenet*2)
            time.sleep(3)

        if twolive > twonet*2 and adjusttwo2x == False:
            print(twonet, twolive," switch first to move forward ",twonet*2)
            closeposition(oneposition)
            setAdjustment(oneposition)
            adjusttwo2x = True
            setHoldings()

        else:
            print(twonet, twolive, "skipping two as not doubled ",twonet*2)
            time.sleep(3)

        if onelive <= onenet*20/100 and one90close == False:
            print(onenet, onelive, " closing one as reaching 80% done ",onenet*20/100)
            placelimitOrder(oneposition,round(onenet * 15 / 100, 1))
            one90close = True
        else:
            print(onenet, onelive,  " skipping one as not touched 80% ",onenet*20/100)
            time.sleep(3)

        if twolive <= twonet*20/100 and two90close == False:
            print(twonet, twolive," closing two as reaching 80% done ",twonet*20/100)
            placelimitOrder(twoposition,round(twonet*15/100,1))
            two90close = True
        else:
            print(twonet, twolive,  " skipping two as not touched 80% ", twonet*20/100)
            time.sleep(3)
        setHoldings()

    while len(holdings_response['positions']) == 1 :
        quote_response = groww.get_quote(
            exchange=groww.EXCHANGE_NSE,
            segment=groww.SEGMENT_FNO,
            trading_symbol=holdings_response['positions'][0]['trading_symbol']
        )
        #print(quote_response['last_price'])

        onelive = quote_response['last_price']
        if onelive > onenet*2 and adjustone2x == False:
            closeposition(oneposition)
            adjustone2x=True
        else:
            print(onenet, onelive,  " skipping one as not doubled ",onenet*2)
            time.sleep(3)

        setHoldings()

    while len(holdings_response['positions']) == 0 :
        print("No Holdings...")

except Exception as e:
    print(f"❌ Failed to place BUY order: {e}")
    exit(1)

