# =====================
# This is a Sample script that places a Buy order, waits 10 seconds, and then places a Sell order.
# =====================
import math
import random
import string
import time
import traceback
from growwapi import GrowwAPI
from datetime import datetime, time as dt_time

# =====================
# STEP 1: Setup
# =====================

# === Setup Groww API ===
# Please use the "Generate API key" option on the API keys page to obtain the API key and Secret.

user_api_key = "user_api_key"
user_secret = "user_secret"

try: 
    access_token = GrowwAPI.get_access_token(api_key=user_api_key, secret=user_secret)
    # Use access_token to initiate GrowwAPI
    groww = GrowwAPI(access_token)
    print("✅ Ready to Groww")
except Exception as e:
    access_token = GrowwAPI.get_access_token(api_key=user_api_key, secret=user_secret)
    # Use access_token to initiate GrowwAPI
    groww = GrowwAPI(access_token)
    print("✅ Ready to Groww retry")

def setAdjustment(position):
    repositionx = 0
    if (position['net_price'] < 10):
        repositionx = 1.2
    elif (position['net_price'] >= 10 and position['net_price'] <= 15):
        repositionx = 1.1
    elif (position['net_price'] > 15):
        repositionx = 1.0
    print(f"📊 ADJUSTMENT MULTIPLIER: {repositionx}x (Entry Price: ₹{position['net_price']})")
    if (position['optionType'] == 'PE'):
        for i in range(15):
            currentspot = int(position['spot']) + i * 50
            new_symbol = position['trading_symbol'].replace(str(position['spot']), str(currentspot))
            print(f"  📈 Iteration {i + 1}/15 | Checking PE Strike: {currentspot} | Symbol: {new_symbol}")
            quote_response = groww.get_quote(
                exchange=groww.EXCHANGE_NSE,
                segment=groww.SEGMENT_FNO,
                trading_symbol=new_symbol
            )
            current_price = quote_response['last_price']
            threshold = position['net_price'] * repositionx
            print(f"     Current Price: ₹{current_price} | Threshold: ₹{threshold:.2f}")
            random_string = new_symbol[-9:]
            if (current_price - threshold > 1):
                print(f"  ✅ ADJUSTMENT TRIGGER HIT! Price exceeded threshold by ₹{current_price - threshold:.2f}")
                adjustOrder(currentspot, position, random_string)
                return currentspot
            else:
                print(f"     ⏳ Not yet profitable (need ₹{threshold - current_price:.2f} more)")
                time.sleep(3)
                continue
    else:
        for i in range(15):
            currentspot = int(position['spot']) - i * 50
            new_symbol = position['trading_symbol'].replace(str(position['spot']), str(currentspot))
            print(f"  📉 Iteration {i + 1}/15 | Checking CE Strike: {currentspot} | Symbol: {new_symbol}")
            quote_response = groww.get_quote(
                exchange=groww.EXCHANGE_NSE,
                segment=groww.SEGMENT_FNO,
                trading_symbol=new_symbol
            )
            current_price = quote_response['last_price']
            threshold = position['net_price'] * repositionx
            print(f"     Current Price: ₹{current_price} | Threshold: ₹{threshold:.2f}")
            random_string = new_symbol[-9:]
            if (current_price - threshold > 1):
                print(f"  ✅ ADJUSTMENT TRIGGER HIT! Price exceeded threshold by ₹{current_price - threshold:.2f}")
                adjustOrder(currentspot, position, random_string)
                return currentspot
            else:
                print(f"     ⏳ Not yet profitable (need ₹{threshold - current_price:.2f} more)")
                time.sleep(3)
                continue

def adjustOrder(currentspot, position, random_string):
    orderList = groww.get_order_list()['order_list']
    orderFound = False
    for order in orderList:
        if order.get('trading_symbol') == position['trading_symbol'].replace(str(position['spot']),
                                                                             str(currentspot)) and order.get(
            'order_status') in ['ACKED', 'EXECUTED', 'PARTIALLY EXECUTED'] and order.get(
            'transaction_type') == 'SELL':
            print(
                f"  ⚠️  EXISTING ORDER FOUND | Order ID: {order.get('order_reference_id')} | Status: {order.get('order_status')}")
            orderFound = True
            random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=9))
            print(f"  🔄 Generated new random string to avoid duplicate: {random_string}")
            return
    if (not orderFound):
        random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=9))
        new_symbol = position['trading_symbol'].replace(str(position['spot']), str(currentspot))
        print(f"  🛒 PLACING SELL ORDER | Symbol: {new_symbol} | Qty: {position['debit_quantity']} | Type: MARKET")
        place_order_response = groww.place_order(
            trading_symbol=new_symbol,
            quantity=position['debit_quantity'],
            validity=groww.VALIDITY_DAY,
            exchange=groww.EXCHANGE_NSE,
            segment=position['segment'],
            product=groww.PRODUCT_NRML,
            order_type=groww.ORDER_TYPE_MARKET,
            transaction_type=groww.TRANSACTION_TYPE_SELL,
            order_reference_id="Ab-" + random_string + "-1628190"
        )
        print(f"  ✅ ORDER PLACED | Response: {place_order_response.get('status', 'Pending')}")

        # Wait for order execution
        is_executed, final_status = wait_for_order_execution(
            groww_order_id=place_order_response['groww_order_id'],
            segment=groww.SEGMENT_FNO,
            max_wait_seconds=60
        )

        if is_executed:
            print(f"  ✅ ORDER SUCCESSFULLY EXECUTED")
            return
        else:
            print(f"  ⚠️  Order did not execute with status: {final_status}")
            retryOnOrderFail(currentspot, place_order_response, position)

def expandAdjustment(position):
    print(f"🔄 EXPAND ADJUSTMENT | Symbol: {position['trading_symbol']} | Entry Price: ₹{position['net_price']}")
    if (position['optionType'] == 'PE'):
        for i in range(15):
            currentspot = int(position['spot']) - (i + 1) * 50
            new_symbol = position['trading_symbol'].replace(str(position['spot']), str(currentspot))
            print(f"  📈 Iteration {i + 1}/15 | Checking Lower PE Strike: {currentspot} | Symbol: {new_symbol}")
            quote_response = groww.get_quote(
                exchange=groww.EXCHANGE_NSE,
                segment=groww.SEGMENT_FNO,
                trading_symbol=new_symbol
            )
            current_price = quote_response['last_price']
            print(f"     Current Price: ₹{current_price} | Threshold: ₹{position['net_price']:.2f}")
            random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=9))
            if (current_price - (position['net_price']) < 1):
                print(f"  ✅ EXPAND TRIGGER HIT! Price is within ₹1 of entry")
                expandOrder(currentspot, position, random_string)
                return currentspot
            else:
                print(f"     ⏳ Price still too high (need ₹{position['net_price'] - current_price:.2f} drop)")
                time.sleep(10)
                continue
    else:
        for i in range(15):
            currentspot = int(position['spot']) + (i + 1) * 50
            new_symbol = position['trading_symbol'].replace(str(position['spot']), str(currentspot))
            print(f"  📉 Iteration {i + 1}/15 | Checking Higher CE Strike: {currentspot} | Symbol: {new_symbol}")
            quote_response = groww.get_quote(
                exchange=groww.EXCHANGE_NSE,
                segment=groww.SEGMENT_FNO,
                trading_symbol=new_symbol
            )
            current_price = quote_response['last_price']
            print(f"     Current Price: ₹{current_price} | Threshold: ₹{position['net_price']:.2f}")
            random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=9))
            if (current_price - (position['net_price']) < 1):
                print(f"  ✅ EXPAND TRIGGER HIT! Price is within ₹1 of entry")
                expandOrder(currentspot, position, random_string)
                return currentspot
            else:
                print(f"     ⏳ Price still too high (need ₹{position['net_price'] - current_price:.2f} drop)")
                time.sleep(3)
                continue

def expandOrder(currentspot, position, random_string):
    print(
        f"🛒 PLACING EXPAND SELL ORDER | Symbol: {position['trading_symbol'].replace(str(position['spot']), str(currentspot))} | Qty: {position['debit_quantity']}")
    orderList = groww.get_order_list()['order_list']
    orderFound = False
    for order in orderList:
        if order.get('trading_symbol') == position['trading_symbol'].replace(str(position['spot']),
                                                                             str(currentspot)) and order.get(
            'order_status') in ['ACKED', 'EXECUTED', 'PARTIALLY EXECUTED'] and order.get(
            'transaction_type') == 'SELL':
            print(
                f"  ⚠️  EXISTING ORDER FOUND | Order ID: {order.get('order_reference_id')} | Status: {order.get('order_status')}")
            orderFound = True
            random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=9))
            print(f"  🔄 Generated new random string: {random_string}")
            return
    if (not orderFound):
        place_order_response = groww.place_order(
            trading_symbol=position['trading_symbol'].replace(str(position['spot']), str(currentspot)),
            quantity=position['debit_quantity'],
            validity=groww.VALIDITY_DAY,
            exchange=groww.EXCHANGE_NSE,
            segment=position['segment'],
            product=groww.PRODUCT_NRML,
            order_type=groww.ORDER_TYPE_MARKET,
            transaction_type=groww.TRANSACTION_TYPE_SELL,
            order_reference_id="Ab-" + random_string + "-1628190"
        )
        print(f"  ✅ EXPAND ORDER PLACED | Status: {place_order_response.get('status', 'Pending')}")

        # Wait for order execution
        is_executed, final_status = wait_for_order_execution(
            groww_order_id=place_order_response['groww_order_id'],
            segment=groww.SEGMENT_FNO,
            max_wait_seconds=60
        )

        if is_executed:
            print(f"  ✅ EXPAND ORDER SUCCESSFULLY EXECUTED")
            return
        else:
            print(f"  ⚠️  Order did not execute with status: {final_status}")
            retryOnOrderFail(currentspot, place_order_response, position)

def moveHedges(position, currentspot):
    print(
        f"🔄 MOVING HEDGE | Position: {position['trading_symbol']} | New Strike: {currentspot} | Entry Price: ₹{position['net_price']}")
    if (position['optionType'] == 'PE'):
        reopenHedge(currentspot - 300, pehedge)
        closehedge(pehedge)
        time.sleep(5)
    elif position['optionType'] == 'CE':
        reopenHedge(currentspot + 300, cehedge)
        closehedge(cehedge)
        time.sleep(5)

def compressWing(position, currentspot, size):
    print(
        f"🔄 MOVING HEDGE | Position: {position['trading_symbol']} | New Strike: {currentspot} | Entry Price: ₹{position['net_price']}")
    if (position['optionType'] == 'PE'):
        reopenHedge(currentspot - size, pehedge)
        closehedge(pehedge)
        time.sleep(5)
    elif position['optionType'] == 'CE':
        reopenHedge(currentspot + size, cehedge)
        closehedge(cehedge)
        time.sleep(5)

def reopenHedge(currentspot, hedge):
    print(f"📂 REOPENING HEDGE | Symbol: {hedge['trading_symbol']} | New Strike: {currentspot}")
    orderList = groww.get_order_list()['order_list']
    orderFound = False
    for order in orderList:
        if order.get('trading_symbol') == hedge['trading_symbol'].replace(str(hedge['spot']),
                                                                          str(currentspot)) and order.get(
            'order_status') in ['ACKED', 'EXECUTED', 'PARTIALLY EXECUTED'] and order.get(
            'transaction_type') == 'BUY':
            print(
                f"  ⚠️  EXISTING ORDER FOUND | Order ID: {order.get('order_reference_id')} | Status: {order.get('order_status')}")
            orderFound = True
            random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=9))
            print(f"  🔄 Generated new random string: {random_string}")
            return
    if (not orderFound):
        random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=9))
        place_order_response = groww.place_order(
            trading_symbol=hedge['trading_symbol'].replace(hedge['spot'], str(currentspot)),
            quantity=hedge['quantity'],
            validity=groww.VALIDITY_DAY,
            exchange=groww.EXCHANGE_NSE,
            segment=hedge['segment'],
            product=groww.PRODUCT_NRML,
            order_type=groww.ORDER_TYPE_MARKET,
            transaction_type=groww.TRANSACTION_TYPE_BUY,
            order_reference_id="Ab-" + random_string + "-1628190"
        )
        print(f"  ✅ HEDGE REOPENED | Status: {place_order_response.get('status', 'Pending')}")

        # Wait for order execution
        is_executed, final_status = wait_for_order_execution(
            groww_order_id=place_order_response['groww_order_id'],
            segment=groww.SEGMENT_FNO,
            max_wait_seconds=60
        )

        if is_executed:
            print(f"  ✅ HEDGE REOPEN ORDER SUCCESSFULLY EXECUTED")
        else:
            print(f"  ⚠️  Hedge reopen order status: {final_status}")

def wait_for_order_execution(groww_order_id, segment, max_wait_seconds=300, check_interval=2):
    """
    Wait for order to be executed. Checks order status until it's EXECUTED or fails.

    Order Status Values:
    - PENDING: Order placed but not yet sent to exchange
    - TRIGGER PENDING: Limit order waiting for trigger price
    - ACKED: Order acknowledged by exchange, not yet executed
    - PARTIALLY EXECUTED: Partial quantity executed
    - EXECUTED: Order fully executed
    - CANCELLED: Order cancelled
    - REJECTED: Order rejected by exchange
    - EXPIRED: Order expired
    """
    EXECUTED_STATUSES = ['EXECUTED', 'PARTIALLY EXECUTED']
    FAILED_STATUSES = ['REJECTED', 'CANCELLED', 'EXPIRED']
    PENDING_STATUSES = ['PENDING', 'TRIGGER PENDING', 'ACKED']

    elapsed_time = 0

    while elapsed_time < max_wait_seconds:
        try:
            order_detail = groww.get_order_detail(
                groww_order_id=groww_order_id,
                segment=segment
            )
            status = order_detail.get('order_status')
            quantity = order_detail.get('filled_quantity', 0)
            total_qty = order_detail.get('quantity', 0)

            print(f"  ⏳ Order Status: {status} | Filled: {quantity}/{total_qty} | Waited: {elapsed_time}s")

            # Check if executed
            if status in EXECUTED_STATUSES:
                print(f"  ✅ ORDER EXECUTED | Status: {status} | Filled: {quantity}/{total_qty}")
                return True, status

            # Check if failed
            elif status in FAILED_STATUSES:
                reason = order_detail.get('remark', 'Unknown reason')
                print(f"  ❌ ORDER {status} | Reason: {reason}")
                return False, status

            # Still pending
            elif status in PENDING_STATUSES:
                print(f"  ⏳ Waiting for execution... ({status})")
                time.sleep(check_interval)
                elapsed_time += check_interval

            else:
                print(f"  ⚠️  Unknown status: {status}")
                time.sleep(check_interval)
                elapsed_time += check_interval

        except Exception as e:
            print(f"  ❌ Error checking order status: {e}")
            time.sleep(check_interval)
            elapsed_time += check_interval

    print(f"  ⏱️  Order execution timeout after {max_wait_seconds}s")
    return False, "TIMEOUT"

def retryOnOrderFail(currentspot, orderResponse, position):
    order_detail_response = groww.get_order_detail(
        groww_order_id=orderResponse['groww_order_id'],
        segment=groww.SEGMENT_FNO,
    )

    # Wait for order execution
    is_executed, final_status = wait_for_order_execution(
        groww_order_id=orderResponse['groww_order_id'],
        segment=groww.SEGMENT_FNO,
        max_wait_seconds=300
    )

    if not is_executed:
        if final_status == 'REJECTED' and "Margin Exceeds" in order_detail_response.get('remark', ''):
            print(f"❌ ORDER REJECTED | Reason: Margin Shortfall | Retrying with reduced qty")
            random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=9))
            quantity_ = position['debit_quantity']
            noofLots = quantity_ / 65
            halflots = int(65 * round(noofLots / 2, 0))
            print(f"  Original Qty: {quantity_} | Lots: {noofLots:.1f} | Half Lots: {halflots}")
            orderResponse = groww.place_order(
                trading_symbol=position['trading_symbol'].replace(str(position['spot']), str(currentspot)),
                quantity=halflots,
                validity=groww.VALIDITY_DAY,
                exchange=groww.EXCHANGE_NSE,
                segment=position['segment'],
                product=groww.PRODUCT_NRML,
                order_type=groww.ORDER_TYPE_MARKET,
                transaction_type=groww.TRANSACTION_TYPE_SELL,
                order_reference_id="Ab-" + random_string + "-1628190"
            )
            print(f"  ✅ RETRY ORDER PLACED | Status: {orderResponse.get('status', 'Pending')}")
            time.sleep(5)

def closeposition(position):
    print(f"🔴 CLOSING POSITION | Symbol: {position['symbol_isin']} | Qty: {position['debit_quantity']}")
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=9))
    orderList = groww.get_order_list()['order_list']
    orderFound = False
    for order in orderList:
        if order.get('trading_symbol') == position['symbol_isin'] and order.get(
                'order_status') == 'ACKED' and order.get('transaction_type') == 'BUY':
            print(f"  ⚠️  EXISTING BUY ORDER FOUND | Order ID: {order.get('order_reference_id')} | Skipping...")
            orderFound = True
            return
    if (not orderFound):
        print(
            f"  🛒 PLACING BUY ORDER | Symbol: {position['symbol_isin']} | Qty: {position['debit_quantity']} | Type: MARKET")
        try:
            place_order_response = groww.place_order(
                trading_symbol=position['symbol_isin'],
                quantity=position['debit_quantity'],
                validity=groww.VALIDITY_DAY,
                exchange=groww.EXCHANGE_NSE,
                segment=position['segment'],
                product=groww.PRODUCT_NRML,
                order_type=groww.ORDER_TYPE_MARKET,
                transaction_type=groww.TRANSACTION_TYPE_BUY,
                order_reference_id="Ab-" + random_string + "-1628190"
            )
            print(f"  ✅ CLOSE ORDER PLACED | Status: {place_order_response.get('status', 'Pending')}")
            time.sleep(10)
            order_detail_response = groww.get_order_detail(
                groww_order_id=place_order_response['groww_order_id'],
                segment=groww.SEGMENT_FNO,
            )
            if order_detail_response['order_status'] == 'ACKED' or order_detail_response[
                'order_status'] == 'TRIGGER PENDING':
                print(f"  ✅ ORDER ACKNOWLEDGED | Status: {order_detail_response['order_status']}")

        except Exception as e:
            s = str(e)
            if "Duplicate order. Order with this reference id already exists" in s:
                random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=9))
                print(f"  ⚠️  DUPLICATE ORDER | Retrying with new reference ID...")
                place_order_response = groww.place_order(
                    trading_symbol=position['symbol_isin'],
                    quantity=position['debit_quantity'],
                    validity=groww.VALIDITY_DAY,
                    exchange=groww.EXCHANGE_NSE,
                    segment=position['segment'],
                    product=groww.PRODUCT_NRML,
                    order_type=groww.ORDER_TYPE_MARKET,
                    transaction_type=groww.TRANSACTION_TYPE_BUY,
                    order_reference_id="Ab-" + random_string + "-1628190"
                )
                print(f"  ✅ RETRY ORDER PLACED | Status: {place_order_response.get('status', 'Pending')}")
        time.sleep(5)

def closehedge(position):
    print(f"🔴 CLOSING HEDGE | Symbol: {position['symbol_isin']} | Qty: {position['quantity']}")
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=9))
    orderList = groww.get_order_list()['order_list']
    orderFound = False
    for order in orderList:
        if order.get('trading_symbol') == position['symbol_isin'] and order.get(
                'order_status') == 'ACKED' and order.get('transaction_type') == 'SELL':
            print(f"  ⚠️  EXISTING SELL ORDER FOUND | Order ID: {order.get('order_reference_id')} | Skipping...")
            orderFound = True
            return
    if (not orderFound):
        print(
            f"  🛒 PLACING SELL ORDER | Symbol: {position['symbol_isin']} | Qty: {position['quantity']} | Type: MARKET")
        try:
            place_order_response = groww.place_order(
                trading_symbol=position['symbol_isin'],
                quantity=position['quantity'],
                validity=groww.VALIDITY_DAY,
                exchange=groww.EXCHANGE_NSE,
                segment=position['segment'],
                product=groww.PRODUCT_NRML,
                order_type=groww.ORDER_TYPE_MARKET,
                transaction_type=groww.TRANSACTION_TYPE_SELL,
                order_reference_id="Ab-" + random_string + "-1628190"
            )
            print(f"  ✅ HEDGE CLOSE ORDER PLACED | Status: {place_order_response.get('status', 'Pending')}")
        except Exception as e:
            s = str(e)
            if "Duplicate order. Order with this reference id already exists" in s:
                random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=9))
                print(f"  ⚠️  DUPLICATE ORDER | Retrying with new reference ID...")
                place_order_response = groww.place_order(
                    trading_symbol=position['symbol_isin'],
                    quantity=position['quantity'],
                    validity=groww.VALIDITY_DAY,
                    exchange=groww.EXCHANGE_NSE,
                    segment=position['segment'],
                    product=groww.PRODUCT_NRML,
                    order_type=groww.ORDER_TYPE_MARKET,
                    transaction_type=groww.TRANSACTION_TYPE_SELL,
                    order_reference_id="Ab-" + random_string + "-1628190"
                )
                print(f"  ✅ RETRY ORDER PLACED | Status: {place_order_response.get('status', 'Pending')}")
    time.sleep(5)

def setHoldings():
    global holdings_response, oneposition, onenet, twoposition, twonet, onedelta, twodelta, pehedge, cehedge

    # Initialize to None to prevent errors if hedges don't exist
    pehedge = None
    cehedge = None

    holdings_response = groww.get_positions_for_user()
    print("\n📋 [SET HOLDINGS] - Raw Holdings from Groww:")
    for position in holdings_response['positions']:
        print(
            f"  • Symbol: {position['symbol_isin']} | Qty: {position['quantity']} | Net Price: ₹{position['net_price']} | Realized PnL: ₹{position['realised_pnl']}")
    print("────────────────────────────────────────────────────────────")

    for item in holdings_response['positions'].copy():
        if item['segment'] != 'FNO' or item['realised_pnl'] != 0.0:
            # removing closed positions and non FNO positions from list
            holdings_response['positions'].remove(item)

    for item in holdings_response['positions'].copy():
        if item['quantity'] >= 0 and item['trading_symbol'].endswith('PE'):
            pehedge = item
            pehedge['spot'] = getpositionInfo(item['trading_symbol'])['strike_price']
            holdings_response['positions'].remove(item)
        elif item['quantity'] >= 0 and item['trading_symbol'].endswith('CE'):
            cehedge = item
            cehedge['spot'] = getpositionInfo(item['trading_symbol'])['strike_price']
            holdings_response['positions'].remove(item)

    print("────────────────────────────────────────────────────────────")

    # Print hedges only if they exist
    if pehedge is not None:
        print(
            f"🛡️  PE Hedge: {pehedge['symbol_isin']} | Qty: {pehedge['quantity']} | Net Price: ₹{pehedge['net_price']} | Realized PnL: ₹{pehedge['realised_pnl']}")
    else:
        print("🛡️  PE Hedge: NOT FOUND")

    if cehedge is not None:
        print(
            f"🛡️  CE Hedge: {cehedge['symbol_isin']} | Qty: {cehedge['quantity']} | Net Price: ₹{cehedge['net_price']} | Realized PnL: ₹{cehedge['realised_pnl']}")
    else:
        print("🛡️  CE Hedge: NOT FOUND")
    print("────────────────────────────────────────────────────────────")
    print("📋 [SET HOLDINGS] - Open Positions:")
    for position in holdings_response['positions']:
        print(
            f"  • Symbol: {position['symbol_isin']} | Qty: {position['quantity']} | Net Price: ₹{position['net_price']} | Realized PnL: ₹{position['realised_pnl']}")
    print("────────────────────────────────────────────────────────────")

    if (len(holdings_response['positions']) > 0):
        oneposition = holdings_response['positions'][0]
        info = getpositionInfo(holdings_response['positions'][0]['trading_symbol'])
        oneposition['net'] = holdings_response['positions'][0]['net_price'];
        oneposition['spot'] = info['strike_price'];
        oneposition['optionType'] = info['instrument_type']
        oneposition['expiry'] = info['expiry_date']
        oneposition['delta'] = getDelta(holdings_response['positions'][0]['trading_symbol'])
        quote_response = groww.get_quote(
            exchange=groww.EXCHANGE_NSE,
            segment=groww.SEGMENT_FNO,
            trading_symbol=holdings_response['positions'][0]['trading_symbol']
        )
        oneposition['live'] = quote_response['last_price']
        print(

            f"Strike: {oneposition['spot']} | Type: {oneposition['optionType']} | Expiry: {oneposition['expiry']} | Net: ₹{oneposition['net']}  | Live: ₹{oneposition['live']} | Delta: {oneposition['delta']}")
        if (len(holdings_response['positions']) > 1):
            twoposition = holdings_response['positions'][1]
            twoposition['net'] = holdings_response['positions'][1]['net_price']
            info = getpositionInfo(holdings_response['positions'][1]['trading_symbol'])
            twoposition['spot'] = info['strike_price']
            twoposition['optionType'] = info['instrument_type']
            twoposition['expiry'] = info['expiry_date']
            twoposition['delta'] = getDelta(holdings_response['positions'][1]['trading_symbol'])
            quote_response = groww.get_quote(
                exchange=groww.EXCHANGE_NSE,
                segment=groww.SEGMENT_FNO,
                trading_symbol=holdings_response['positions'][1]['trading_symbol']
            )
            twoposition['live'] = quote_response['last_price']
            print(
                f" Strike: {twoposition['spot']} | Type: {twoposition['optionType']} | Expiry: {twoposition['expiry']} | Net: ₹{twoposition['net']} | Live: ₹{twoposition['live']} | Delta: {twoposition['delta']}")
        print(f"Total Open Positions: {len(holdings_response['positions'])}")

def getDelta(tradingSymbol):
    get_instrument_by_trading_symbol_response = getpositionInfo(tradingSymbol)
    greeks = (groww.get_greeks(exchange=groww.EXCHANGE_NSE,
                               underlying="NIFTY",
                               trading_symbol=tradingSymbol,
                               expiry=get_instrument_by_trading_symbol_response['expiry_date']
                               ))

    deltaValue = round(math.fabs(greeks['greeks']['delta']), 2);
    return deltaValue;

def getpositionInfo(tradingSymbol):
    get_instrument_by_trading_symbol_response = groww.get_instrument_by_exchange_and_trading_symbol(
        exchange=groww.EXCHANGE_NSE,
        trading_symbol=tradingSymbol
    )
    return get_instrument_by_trading_symbol_response

def placelimitOrder(position, limitValue):
    global length, random_string, place_order_response
    length = 9
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=9))

    print("placing order ", position['symbol_isin'], position['debit_quantity'], position['segment'],
          groww.ORDER_TYPE_LIMIT, limitValue, groww.TRANSACTION_TYPE_BUY)
    place_order_response = groww.place_order(
        trading_symbol=position['symbol_isin'],
        quantity=position['debit_quantity'],
        validity=groww.VALIDITY_DAY,
        exchange=groww.EXCHANGE_NSE,
        segment=position['segment'],
        product=groww.PRODUCT_NRML,
        order_type=groww.ORDER_TYPE_LIMIT,
        price=limitValue,
        transaction_type=groww.TRANSACTION_TYPE_BUY,
        order_reference_id="Ab-" + random_string + "-1628190"
    )
    print(place_order_response)
    time.sleep(5)

while True:
    try:
        # ===== MARKET HOURS CHECK =====
        current_time = datetime.now()
        market_start = dt_time(9, 30)  # 9:30 AM
        market_end = dt_time(15, 00)   # 3:30 PM

        # Check if current time is before market open
        if current_time.time() < market_start:
            print(f"⏰ Market not open yet. Current time: {current_time.strftime('%H:%M:%S')} | Market opens at 09:30:00")
            time.sleep(60)  # Wait 1 minute before checking again
            continue  # Skip to next iteration

        # Check if market is closed
        if current_time.time() > market_end:
            print(f"🔴 Market closed. Current time: {current_time.strftime('%H:%M:%S')} | Market closed at 15:30:00")
            time.sleep(60)
            continue

        # Check if weekend
        if current_time.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            print(f"📅 Weekend - Market closed. Today is {current_time.strftime('%A')}")
            time.sleep(300)  # Wait 5 minutes on weekends
            continue

        print(f"✅ Market is open - Executing strategy at {current_time.strftime('%H:%M:%S')}")

        setHoldings()

        one90close = False
        two90close = False

        while len(holdings_response['positions']) >= 2:
            onelive = oneposition['live']
            onenet = oneposition['net']
            onedelta = oneposition['delta']
            twolive = twoposition['live']
            twonet = twoposition['net']
            twodelta = twoposition['delta']

            # Section 1: 1.75x Exit Logic
            # Position 1
            c1 = onelive > onenet * 1.75
            c2 = onedelta >= 0.15
            c3 = twolive < twonet * 0.9
            met_count = sum([c1, c2, c3])

            if c1 and c2 and c3:
                print(f"Position 1 exit conditions MET (3/3): adjusting other side and compressing wing 100")
                #closeposition(twoposition)
                #adjustment = setAdjustment(twoposition)
                #moveHedges(twoposition, adjustment)
                #compressWing(oneposition,oneposition['strike_price'],100)

                closeposition(oneposition)
                if oneposition['optionType'] == 'PE' and pehedge is not None:
                    closehedge(pehedge)
                elif oneposition['optionType'] == 'CE' and cehedge is not None:
                    closehedge(cehedge)

                setHoldings()
            else:
                print(f"Position 1 exit: {met_count}/3 conditions met.")
                print(f"  - Price (>1.75x): {'Condition [MET]' if c1 else '[PENDING]'} ({onelive:.2f} > {onenet * 1.75:.2f})")
                print(f"  - Delta (>0.15):  {'Condition [MET]' if c2 else '[PENDING]'} ({onedelta:.2f})")
                print(f"  - Opp. (<0.9x):   {'Condition [MET]' if c3 else '[PENDING]'} ({twolive:.2f} < {twonet * 0.9:.2f})")

            # Position 2
            c1 = twolive > twonet * 1.75
            c2 = twodelta >= 0.15
            c3 = onelive < onenet * 0.9
            met_count = sum([c1, c2, c3])

            if c1 and c2 and c3:
                print(f"Position 2 exit conditions MET (3/3): adjusting other side and compressing wing 100")
                #closeposition(oneposition)
                #adjustment = setAdjustment(oneposition)
                #moveHedges(oneposition, adjustment)
                #compressWing(twoposition,twoposition['strike_price'],100)

                closeposition(twoposition)
                if twoposition['optionType'] == 'PE' and pehedge is not None:
                    closehedge(pehedge)
                elif twoposition['optionType'] == 'CE' and cehedge is not None:
                    closehedge(cehedge)

                setHoldings()
            else:
                print(f"Position 2 exit: {met_count}/3 conditions met.")
                print(f"  - Price (>1.75x): {'Condition [MET]' if c1 else '[PENDING]'} ({twolive:.2f} > {twonet * 1.75:.2f})")
                print(f"  - Delta (>0.15):  {'Condition [MET]' if c2 else '[PENDING]'} ({twodelta:.2f})")
                print(f"  - Opp. (<0.9x):   {'Condition [MET]' if c3 else '[PENDING]'} ({onelive:.2f} < {onenet * 0.9:.2f})")

            print("-------------------------------------")

            # Section 2: 1.5x Switch Logic
            # Position 1
            c1 = onelive > onenet * 1.5
            c2 = onedelta >= 0.10
            c3 = twolive < twonet * 0.9
            met_count = sum([c1, c2, c3])

            if c1 and c2 and c3:
                print(f"Position 1 switch conditions MET (3/3): Switching")
                #closeposition(twoposition)
                #adjustment = setAdjustment(twoposition)
                #moveHedges(twoposition, adjustment)
                #compressWing(oneposition,oneposition['strike_price'],200)
                closeposition(oneposition)
                if oneposition['optionType'] == 'PE' and pehedge is not None:
                    closehedge(pehedge)
                elif oneposition['optionType'] == 'CE' and cehedge is not None:
                    closehedge(cehedge)

                
                setHoldings()
            else:
                print(f"Position 1 switch: {met_count}/3 conditions met.")
                print(f"  - Price (>1.5x):  {'Condition [MET]' if c1 else '[PENDING]'} ({onelive:.2f} > {onenet * 1.5:.2f})")
                print(f"  - Delta (>0.10):  {'Condition [MET]' if c2 else '[PENDING]'} ({onedelta:.2f})")
                print(f"  - Opp. (<0.9x):   {'Condition [MET]' if c3 else '[PENDING]'} ({twolive:.2f} < {twonet * 0.9:.2f})")

            # Position 2
            c1 = twolive > twonet * 1.5
            c2 = twodelta >= 0.10
            c3 = onelive < onenet * 0.9
            met_count = sum([c1, c2, c3])

            if c1 and c2 and c3:
                print(f"Position 2 switch conditions MET (3/3): Switching")
                #closeposition(oneposition)
                #adjustment = setAdjustment(oneposition)
                #moveHedges(oneposition, adjustment)
                #compressWing(twoposition,twoposition['strike_price'],200)

                closeposition(twoposition)
                if twoposition['optionType'] == 'PE' and pehedge is not None:
                    closehedge(pehedge)
                elif twoposition['optionType'] == 'CE' and cehedge is not None:
                    closehedge(cehedge)

                setHoldings()
            else:
                print(f"Position 2 switch: {met_count}/3 conditions met.")
                print(f"  - Price (>1.5x):  {'Condition [MET]' if c1 else '[PENDING]'} ({twolive:.2f} > {twonet * 1.5:.2f})")
                print(f"  - Delta (>0.10):  {'Condition [MET]' if c2 else '[PENDING]'} ({twodelta:.2f})")
                print(f"  - Opp. (<0.9x):   {'Condition [MET]' if c3 else '[PENDING]'} ({onelive:.2f} < {onenet * 0.9:.2f})")

            print("-------------------------------------")

            # Section 3: 80% Close Logic
            # Position 1
            c1 = onelive <= onenet * 0.2
            c2 = one90close == False
            met_count = sum([c1, c2])

            if c1 and c2:
                print(f"Position 1 close conditions MET (2/2): Closing")
                closeposition(oneposition)
                if oneposition['optionType'] == 'PE' and pehedge: closehedge(pehedge)
                elif oneposition['optionType'] == 'CE' and cehedge: closehedge(cehedge)
                one90close = True
            else:
                print(f"Position 1 close: {met_count}/2 conditions met.")
                print(f"  - Price (<0.2x):  {'Condition [MET]' if c1 else '[PENDING]'} ({onelive:.2f} <= {onenet * 0.2:.2f})")
                print(f"  - Not Closed:     {'Condition [MET]' if c2 else '[DONE/ALREADY CLOSED]'}")

            # Position 2
            c1 = twolive <= twonet * 0.2
            c2 = two90close == False
            met_count = sum([c1, c2])

            if c1 and c2:
                print(f"Position 2 close conditions MET (2/2): Closing")
                closeposition(twoposition)
                if twoposition['optionType'] == 'PE' and pehedge: closehedge(pehedge)
                elif twoposition['optionType'] == 'CE' and cehedge: closehedge(cehedge)
                two90close = True
            else:
                print(f"Position 2 close: {met_count}/2 conditions met.")
                print(f"  - Price (<0.2x):  {'Condition [MET]' if c1 else '[PENDING]'} ({twolive:.2f} <= {twonet * 0.2:.2f})")
                print(f"  - Not Closed:     {'Condition [MET]' if c2 else '[DONE/ALREADY CLOSED]'}")
            
            print("-------------------------------------")
            oneposition['profitperecentage'] = round(((onenet - onelive) / onenet) * 100, 0)
            twoposition['profitperecentage'] = round(((twonet - twolive) / twonet) * 100, 0)
            print(oneposition['optionType'] ,"net ", onenet, oneposition['optionType'],"live ", onelive, oneposition['optionType'],"  position profit at ", oneposition['profitperecentage'],
                  "%")
            print(twoposition['optionType'],"net ", twonet, twoposition['optionType'],"live ", twolive, twoposition['optionType']," position profit at ", twoposition['profitperecentage'],
                  "%")

            oneposition['debit_quantity'] = -1 * oneposition['quantity']
            twoposition['debit_quantity'] = -1 * twoposition['quantity']
            oneprofit = (onenet * oneposition['debit_quantity']) - (onelive * oneposition['debit_quantity'])
            twoprofit = (twonet * twoposition['debit_quantity']) - (twolive * twoposition['debit_quantity'])
            liveProfit = round((oneprofit + twoprofit), 2)
            print("Live profit is ", liveProfit)
            print("-------------------------------------")

            totalProfit = round((onenet * oneposition['debit_quantity']) + (twonet * twoposition['debit_quantity']), 0)

            liveprofitPercentage = oneposition['profitperecentage'] + twoposition['profitperecentage']

            print("target profit at 75% ", totalProfit * 75 / 100)
            print("stop loss at 25% ", -1 * totalProfit * 25 / 100)

            if liveProfit >= totalProfit * 0.75:
                print("Closing orders as target profit has hit ", totalProfit * 0.75)
                closeposition(oneposition)
                closeposition(twoposition)
                if pehedge is not None:
                    closehedge(pehedge)
                if cehedge is not None:
                    closehedge(cehedge)
            else:
                print("Skipping closing position as target profit ", totalProfit * 0.75, " not hit currently at ",
                      liveProfit)

            print("-------------------------------------")

            stoplossValue = totalProfit * 0.25

            # Calculate current hedge prices (with safety checks)
            pehedge_current = None
            cehedge_current = None

            if pehedge is not None:
                try:
                    pehedge_quote = groww.get_quote(
                        exchange=groww.EXCHANGE_NSE,
                        segment=groww.SEGMENT_FNO,
                        trading_symbol=pehedge['symbol_isin']
                    )
                    pehedge_current = pehedge_quote['last_price']
                except:
                    pehedge_current = None
                    print("⚠️  Could not fetch PE hedge current price")

            if cehedge is not None:
                try:
                    cehedge_quote = groww.get_quote(
                        exchange=groww.EXCHANGE_NSE,
                        segment=groww.SEGMENT_FNO,
                        trading_symbol=cehedge['symbol_isin']
                    )
                    cehedge_current = cehedge_quote['last_price']
                except:
                    cehedge_current = None
                    print("⚠️  Could not fetch CE hedge current price")

            # CORRECT STOP LOSS CONDITION:
            # Trigger when: loss threshold hit AND combined delta indicates significant movement
            if liveProfit <= -1 * stoplossValue and (onedelta + twodelta > 0.25):
                print("🔴 STOP LOSS HIT - BOTH DELTAS INDICATE SIGNIFICANT MOVEMENT")
                print(f"   Combined Delta: {onedelta + twodelta} > 0.25 ✅")
                print(f"   Loss: {liveProfit} | Stop Loss Threshold: -{stoplossValue}")
                if pehedge is not None and pehedge_current is not None:
                    print(f"   PE Hedge Entry: ₹{pehedge['net_price']} | Current: ₹{pehedge_current}")
                if cehedge is not None and cehedge_current is not None:
                    print(f"   CE Hedge Entry: ₹{cehedge['net_price']} | Current: ₹{cehedge_current}")
                closeposition(oneposition)
                closeposition(twoposition)
                if pehedge is not None:
                    closehedge(pehedge)
                if cehedge is not None:
                    closehedge(cehedge)
            else:
                reason = ""
                if liveProfit > -1 * stoplossValue:
                    reason += f"Threshold not hit (loss ₹{liveProfit} > -₹{stoplossValue})"
                if onedelta + twodelta <= 0.25:
                    if reason:
                        reason += " AND "
                    reason += f"Combined delta ({onedelta + twodelta} <= 0.25)"
                print(f"⚠️  SL SKIPPED - {reason}")
                print(f"   Current Loss: ₹{liveProfit} | Stop Loss Threshold: -₹{stoplossValue}")
                print(f" {oneposition['optionType']}  Delta: {onedelta} | {twoposition['optionType']} Delta: {twodelta} | Combined: {onedelta + twodelta} | Required: > 0.3")

            print("-------------------------------------")

            setHoldings()

        while len(holdings_response['positions']) == 1:
            onelive = oneposition['live']
            onenet = oneposition['net']
            onedelta = oneposition['delta']

            if onelive > onenet * 1.75 and onedelta > 0.15:
                print(oneposition['optionType'],"net ", onenet, oneposition['optionType'],"live ", onelive, " Exiting ",oneposition['optionType']," as price to 1.75x ",
                      round(onenet * 1.75, 2))
                print(oneposition['optionType'],"delta ", onedelta, " is greater than 0.15")
                #closeposition(oneposition)
                #adjustment = expandAdjustment(oneposition)
                #moveHedges(oneposition, adjustment)
                
                closeposition(oneposition)
                if oneposition['optionType'] == 'PE' and pehedge is not None:
                    closehedge(pehedge)
                elif oneposition['optionType'] == 'CE' and cehedge is not None:
                    closehedge(cehedge)
                
                setHoldings()
            else:
                print(onenet, onelive, " skipping ",oneposition['optionType']," as not 1.75x ", round(onenet * 1.75, 2))
                print(oneposition['optionType'],"delta ", onedelta, " is less than 0.15")
                time.sleep(5)

            if onelive <= onenet * 0.2 and one90close == False:
                print(onenet, onelive, " closing ",oneposition['optionType']," as reaching 80% done ", round(onenet * 0.2, 2))
                closeposition(oneposition)
                if oneposition['optionType'] == 'PE' and pehedge is not None:
                    closehedge(pehedge)
                elif oneposition['optionType'] == 'CE' and cehedge is not None:
                    closehedge(cehedge)
                one90close = True
            else:
                print(onenet, onelive, " skipping one as not touched 80% ", round(onenet * 0.2, 2))

            oneposition['profitperecentage'] = round(((onenet - onelive) / onenet) * 100, 0)
            print(onenet, onelive, oneposition['optionType'],"  position profit at ", oneposition['profitperecentage'], "%")

            oneprofit = (onenet * oneposition['debit_quantity']) - (onelive * oneposition['debit_quantity'])
            liveProfit = round((oneprofit), 2)
            totalProfit = round((onenet * oneposition['debit_quantity']), 0)

            liveprofitPercentage = oneposition['profitperecentage']

            print("target profit at 75% ", totalProfit * 75 / 100)
            print("stop loss at 25% ", -1 * totalProfit * 25 / 100)

            if liveProfit >= totalProfit * 0.75:
                print("Closing orders as target profit has hit ", totalProfit * 0.75)
                closeposition(oneposition)
                if oneposition['optionType'] == 'PE' and pehedge is not None:
                    closehedge(pehedge)
                elif oneposition['optionType'] == 'CE' and cehedge is not None:
                    closehedge(cehedge)
            else:
                print("Skipping closing position as target profit ", totalProfit * 0.75, " not hit currently at ",
                      liveProfit)

            print("-------------------------------------")

            stoplossValue = totalProfit * 0.25

            if liveProfit <= -1 * stoplossValue and onedelta > 0.15:
                print("🔴 STOP LOSS HIT - CLOSING ALL POSITIONS")
                print(f"   Loss: {liveProfit} | Stop Loss Threshold: -{stoplossValue}")
                print(f"   Delta: {onedelta} > 0.15: YES ✅")
                closeposition(oneposition)
                if oneposition['optionType'] == 'PE' and pehedge is not None:
                    closehedge(pehedge)
                elif oneposition['optionType'] == 'CE' and cehedge is not None:
                    closehedge(cehedge)
            else:
                reason = ""
                if liveProfit > -1 * stoplossValue:
                    reason += "Loss threshold not hit (loss < stop loss limit)"
                if onedelta <= 0.15:
                    if reason:
                        reason += " AND "
                    reason += "Delta <= 0.15 (low sensitivity)"
                print(f"⚠️  STOP LOSS SKIPPED - {reason}")
                print(f"   Current Loss: ₹{liveProfit} | Stop Loss Threshold: -₹{stoplossValue}")
                print(f"   Delta: {onedelta} | Required: > 0.2")

            print("-------------------------------------")

            setHoldings()

        while len(holdings_response['positions']) == 0:
            print("No Holdings...")
            setHoldings()

    except Exception as e:
        print(f"❌ Error occured in options adjustment: {type(e).__name__}: {e}")
        traceback.print_exc()
