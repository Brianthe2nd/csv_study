import mt5linux as mt5
from datetime import datetime,timedelta
# def recalculate_risk(entry_time,pair_name,pip_risk,ai_pair_name):
#     pass

import csv
from datetime import datetime
import os
# from main import Print
from std_out import Print,play_error_sound,log_exception
# from gemini import confirm_pair
def init(terminal_path):
    
    mt5.initialize(path=terminal_path)


def map_pairs (pair):
    pair = pair.lower().strip()
    if pair == "micro_gold" or "gc" in pair or pair == "btcusd" or pair == "gold" or pair == "xauusd" or pair == "mgc":
        # if pair == "micro_gold" or pair == "mgc":
        #     return "BTCUSD"
        # else :
        #     return "BTCUSD" 
        return "XAUUSD"
    elif pair == "crude_oil" or "cl" in pair or pair == "micro_crude_oil" or pair == "ethusd" or pair == "xtiusd" or pair == "mcl":
        # if pair == "micro_crude_oil" or pair == "mcl":
        #     return "ETHUSD"
        # else:
        #     return "ETHUSD"
        return "XTIUSD"
    elif pair == "micro_nasdaq" or pair == "nasdaq" or "nq" in pair or pair == "tech100" or pair == "us100" or pair == "ltcusd" or pair == "mnq":
        # if pair == "micro_nasdaq" or pair == "mnq":
        #     return "LTCUSD"
        # else:
        #     return "LTCUSD"
        # return "LTCUSD"
        return "US100"
    elif "spy" in pair or "es" in pair or pair == "bchusd" or pair == "us500" or pair == "mes":
        # if pair == "micro_spy_500" or pair == "mes": 
        #     return "BCHUSD"
        # else:
        #     return "BCHUSD"
        return "US500" 
    elif "dow" in pair or "ym" in pair or pair == "xrpusd" or pair == "us30":
        # return  "XRPUSD"
        return "US30"
    
    else :
        Print("unknown pair",pair)
        return pair


def log_trade_action(action_type, symbol, volume, price, trade_type, sl, tp, comment="", ticket=None, filepath="trade_log.csv",ai_pair_name="non" ,video = ""):
    """
    Logs a trade action to a CSV file.

    :param action_type: "open", "close", "update"
    :param symbol: Symbol name (e.g., "EURUSD")
    :param volume: Trade volume (lots)
    :param price: Price at which the trade action occurred
    :param trade_type: "buy" or "sell"
    :param comment: Optional comment or reason
    :param ticket: Optional order/position ticket ID
    :param filepath: Filepath of the CSV log
    """
    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action_type,
        "ticket": ticket or "N/A",
        "symbol": symbol,
        "trade_type": trade_type,
        "volume": volume,
        "price": price,
        "sl":sl,
        "tp":tp,
        "comment": comment,
        "ai_pair_name": ai_pair_name,
        "video": video
    }

    # If file doesn't exist, write headers first
    file_exists = os.path.isfile(filepath)
    with open(filepath, mode="a", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=log_entry.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(log_entry)



def get_price_at_time(pair_name,  trade_type, seconds_range=(15, 30)):
    """
    Gets the worst price (highest bid for sell, lowest ask for buy) between entry_time - seconds_range[1]
    and entry_time - seconds_range[0].

    :param pair_name: Symbol name
    :param entry_time: datetime object of entry
    :param trade_type: "buy" or "sell"
    :param seconds_range: Tuple (start, end) in seconds before entry_time
    :return: worst price in the range or None
    """
    entry_time = datetime.now()
    start_time = entry_time - timedelta(seconds=seconds_range[1])
    end_time = entry_time - timedelta(seconds=seconds_range[0])

    ticks = mt5.copy_ticks_range(pair_name,
                                  start_time,
                                  end_time,
                                  mt5.COPY_TICKS_ALL)
    # Print("__TICKS__")
    # Print (ticks)   
    if ticks is None or len(ticks) == 0:
        Print("No tick data found in the given time range.",log_path = "mt5_errors.txt")
        return None

    if trade_type == "buy":
        # For buy, worst price is highest ask
        worst_price = max(tick['ask'] for tick in ticks if tick['ask'] > 0)
    else:
        # For sell, worst price is lowest bid
        worst_price = min(tick['bid'] for tick in ticks if tick['bid'] > 0)

    return worst_price

def recalculate_risk(time_taken, latency, pair_name, pip_risk, ai_pair_name, trader_id, risk=0.4, video=""):
    Print("Recalculating risk...")
    Print("Pair name:", pair_name)
    Print("AI pair name:", ai_pair_name)
    Print("Time taken:", time_taken)
    Print("Latency:", latency)
    Print("Pip risk:", pip_risk)

    pair_name = map_pairs(pair_name)
    # if is_micro:
    #     pair_name = confirm_pair(pair_name)
    positions = mt5.positions_get(symbol=pair_name)
    if not positions:
        Print(f"No open positions found for {pair_name}", log_path="mt5_errors.txt")
        return

    symbol_info = mt5.symbol_info(pair_name)
    if symbol_info is None:
        Print("Failed to get symbol info.", log_path="mt5_errors.txt")
        return

    volume_min = symbol_info.volume_min
    volume_step = symbol_info.volume_step

    account = mt5.account_info()
    if account is None:
        Print("Could not fetch account info.", log_path="mt5_errors.txt")
        return

    total_risk_capital = (risk / 100.0) * account.balance
    Print(f"Total available risk capital: {total_risk_capital:.2f}")

    expected_comment_prefix = f"{trader_id}_{pair_name}"

    for pos in positions:
        if expected_comment_prefix not in pos.comment:
            Print(f"Skipping position with comment {pos.comment}")
            continue  # Only process trades for the specific trader

        trade_type = "buy" if pos.type == mt5.ORDER_TYPE_BUY else "sell"
        latency = (latency[0] + time_taken, latency[1] + time_taken)
        entry_price = get_price_at_time(pair_name, trade_type, latency)
        if entry_price is None:
            Print(f"Failed to get entry price for {pair_name}")
            return

        sl_price = entry_price - pip_risk if trade_type == "buy" else entry_price + pip_risk
        Print(f"Entry price: {entry_price}, SL price: {sl_price}")

        # Update SL if necessary
        update_trade(pair_name, "sl", sl_price, ai_pair_name, trader_id, real_name=True, video=video)

        current_volume = pos.volume
        current_risk = abs(mt5.order_calc_profit(
            mt5.ORDER_TYPE_SELL if trade_type == "buy" else mt5.ORDER_TYPE_BUY,
            pair_name,
            current_volume,
            float(pos.price_open),
            float(sl_price)
        ))

        Print(f"Current risk on existing volume ({current_volume}): {current_risk:.2f}")

        remaining_risk = total_risk_capital - current_risk
        if remaining_risk < 0:
            Print("Current position exceeds risk limit.")
            excess_risk = abs(remaining_risk)

            risk_per_lot = abs(mt5.order_calc_profit(
                mt5.ORDER_TYPE_SELL if trade_type == "buy" else mt5.ORDER_TYPE_BUY,
                pair_name,
                1.0,
                float(entry_price),
                float(sl_price)
            ))

            if risk_per_lot == 0:
                Print("Risk per lot is zero. Cannot adjust.")
                continue

            volume_to_close_raw = excess_risk / risk_per_lot
            steps = int(volume_to_close_raw / volume_step)
            volume_to_close = round(steps * volume_step, 2)

            if volume_to_close < volume_min:
                Print(f"Calculated volume to close ({volume_to_close}) is below min lot size. Skipping.")
                continue

            Print(f"Closing {volume_to_close} to reduce risk to acceptable level.")
            close_type = mt5.ORDER_TYPE_SELL if trade_type == "buy" else mt5.ORDER_TYPE_BUY
            close_price = mt5.symbol_info_tick(pair_name).bid if close_type == mt5.ORDER_TYPE_SELL else mt5.symbol_info_tick(pair_name).ask

            close_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pair_name,
                "volume": volume_to_close,
                "type": close_type,
                "position": pos.ticket,
                "price": close_price,
                "deviation": 100,
                "magic": 123456,
                "comment": f"ReduceRisk_{expected_comment_prefix}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK
            }
            Print(close_request)

            result = mt5.order_send(close_request)
            if result == None:
                Print("Close order failed")
                Print(mt5.last_error())
                return None
            log_trade_action("close", pair_name, volume_to_close, close_price, close_type, sl_price, 0, close_request["comment"], result.order, filepath="trade_log.csv", ai_pair_name=ai_pair_name, video=video)

            if result.retcode == mt5.TRADE_RETCODE_DONE:
                Print(f"Successfully reduced risk by closing {volume_to_close} lots.")
            else:
                Print(f"Failed to close partial position: {result.retcode}", log_path="mt5_errors.txt")
            continue  # Don't add more if already over risk

        risk_per_lot = abs(mt5.order_calc_profit(
            mt5.ORDER_TYPE_SELL if trade_type == "buy" else mt5.ORDER_TYPE_BUY,
            pair_name,
            1.0,
            float(entry_price),
            float(sl_price)
        ))

        if risk_per_lot == 0:
            Print("Risk per lot is zero. Aborting.")
            continue

        additional_volume_raw = remaining_risk / risk_per_lot
        steps = int((additional_volume_raw - volume_min) / volume_step)
        additional_volume = round(volume_min + steps * volume_step, 2)

        if additional_volume < volume_min:
            Print("Additional volume is below minimum lot size. Skipping.")
            continue

        Print(f"Remaining risk capital: {remaining_risk:.2f}, Additional volume to open: {additional_volume}")

        add_type = mt5.ORDER_TYPE_BUY if trade_type == "buy" else mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(pair_name).ask if add_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(pair_name).bid

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pair_name,
            "volume": additional_volume,
            "type": add_type,
            "price": price,
            "deviation": 100,
            "magic": 123456,
            "comment": f"Added_{expected_comment_prefix}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
            "sl": sl_price
        }
        Print(request)
        for i in range(10):
            info = mt5.symbol_info_tick(pair_name)
            request["price"] = info.bid if add_type == mt5.ORDER_TYPE_BUY else info.ask 
            result = mt5.order_send(request)
            if result is None:
                Print("Open order failed")
                Print(mt5.last_error())
                return None
                # return None
            if result.retcode != mt5.TRADE_RETCODE_REQUOTE and result.retcode != mt5.TRADE_RETCODE_PRICE_OFF:
                break
        


        log_trade_action("open", pair_name, additional_volume, price, add_type, sl_price, 0, request["comment"], result.order, filepath="trade_log.csv", ai_pair_name=ai_pair_name, video=video)

        if result.retcode == mt5.TRADE_RETCODE_DONE:
            Print(f"Successfully added {additional_volume} lots.")
        else:
            Print(f"Failed to open additional trade: {result.retcode}", log_path="mt5_errors.txt")



# def update_trade(pair_name,level_type, level_value,ai_pair_name):
#     pass


def update_trade(pair_name, level_type, level_value, ai_pair_name, trader_id, real_name=False, video=""):
    if not real_name:
        pair_name = map_pairs(pair_name)

    positions = mt5.positions_get(symbol=pair_name)
    if not positions:
        Print(f"No open positions found for {pair_name}", log_path="mt5_errors.txt")
        return

    expected_comment_prefix = f"{trader_id}_{pair_name}"

    for pos in positions:
        if expected_comment_prefix not in pos.comment:
            continue  # Skip trades that don't belong to this trader

        new_sl = pos.sl
        new_tp = pos.tp

        if level_type == "sl":
            if new_sl == level_value:
                Print(f"SL already set to {level_value}")
                continue
            new_sl = level_value
        elif level_type == "tp":
            if new_tp == level_value:
                Print(f"TP already set to {level_value}")
                continue
            new_tp = level_value
        else:
            Print(f"Invalid level_type: {level_type}")
            continue

        modify_request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": pos.ticket,
            "symbol": pair_name,
            "sl": float(new_sl),
            "tp": float(new_tp),
            "magic": pos.magic,
            "comment": f"Update by {expected_comment_prefix}"
        }
        Print(modify_request)

        result = mt5.order_send(modify_request)
        if result == None:
            Print("Open order failed")
            Print(mt5.last_error())
            return None

        log_trade_action(
            "update", pair_name, pos.volume, pos.price_open,
            "buy" if pos.type == mt5.ORDER_TYPE_BUY else "sell",
            pos.sl, pos.tp, comment=modify_request["comment"],
            ticket=pos.ticket, filepath="trade_log.csv",
            ai_pair_name=ai_pair_name, video=video
        )

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            Print(f"Failed to update {level_type} for position {pos.ticket}: {result.retcode}", log_path="mt5_errors.txt")
        else:
            Print(f"Updated {level_type.upper()} for position {pos.ticket} to {level_value}", log_path="mt5_errors.txt")


# def open_trade(pair_name,trade_type,ai_pair_name):
#     pass

def open_trade(pair_name, trade_type, ai_pair_name, trader_id, video ,risk = None):
    if risk != None:
        volume = 0.05
    else :
        volume = 0.1
    pair_name = map_pairs(pair_name)
    
    
    if not mt5.symbol_select(pair_name, True):
        Print(f"Symbol {pair_name} not found or not available.", log_path="mt5_errors.txt")
        return None

    tick = mt5.symbol_info_tick(pair_name)
    if tick is None:
        Print(f"Failed to get tick data for {pair_name}", log_path="mt5_errors.txt")
        return None
    symbol_info = mt5.symbol_info(pair_name)
    if symbol_info is None:
        Print("Failed to get symbol info.", log_path="mt5_errors.txt")
        return

    volume_min = symbol_info.volume_min
    if volume < volume_min:
        volume = volume_min
    price = tick.ask if trade_type.lower() == "buy" else tick.bid
    order_type = mt5.ORDER_TYPE_BUY if trade_type.lower() == "buy" else mt5.ORDER_TYPE_SELL

    comment = f"opened_{trader_id}_{ai_pair_name}"

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": pair_name.strip(),
        "volume": volume,
        "type": order_type,
        "price": price,
        "deviation": 100,
        "magic": 123456,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK
    }
    Print(request)
    # result = mt5.order_send(request)
    for i in range(10):
        info = mt5.symbol_info_tick(pair_name)
        request["price"] = info.bid if order_type == mt5.ORDER_TYPE_BUY else info.ask 
        result = mt5.order_send(request)
        if result is None:
            Print("Open order failed")
            Print(mt5.last_error())
            return None
            # return None
        if result.retcode != mt5.TRADE_RETCODE_REQUOTE and result.retcode != mt5.TRADE_RETCODE_PRICE_OFF:
            break
    # if result == None:
    #     Print("Open order failed")
    #     Print(mt5.last_error())
    #     return None

    log_trade_action(
        "open", pair_name, 0.1, price, trade_type,
        0, 0,comment, result.order,
        filepath="trade_log.csv", ai_pair_name=ai_pair_name, video=video
    )

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        Print(f"Order failed: retcode={result.retcode}", log_path="mt5_errors.txt")
        return None
    else:
        Print(f"Order placed: {trade_type.upper()} {pair_name} at {price}", log_path="mt5_errors.txt")
        return result.order  # <-- Return the MT5 ticket number


# def close_trade(pair_name,ai_pair_name):
#     pass


def close_trade(pair_name, ai_pair_name, trader_id, video):
    Print("close trade called")
    Print("Pair name", pair_name)
    Print("AI pair name", ai_pair_name)
    Print("Trader id", trader_id)
    Print("Video", video)
    
    pair_name = map_pairs(pair_name)
    # if is_micro:
    #     pair_name = confirm_pair(pair_name)

    # Get all open positions for the symbol
    positions = mt5.positions_get(symbol=pair_name)
    if positions is None or len(positions) == 0:
        Print(f"No open positions found for {pair_name}", log_path="mt5_errors.txt")
        return

    # Define the unique comment pattern we used in open_trade
    expected_comment_prefix = f"{trader_id}_{pair_name}"

    for pos in positions:
        if expected_comment_prefix not in pos.comment:
            Print("Skipping position with unexpected comment", log_path="mt5_errors.txt")
            continue  # Skip positions not belonging to this trader

        order_type = (
            mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        )
        tick = mt5.symbol_info_tick(pair_name)
        price = tick.bid if order_type == mt5.ORDER_TYPE_SELL else tick.ask

        close_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pair_name,
            "volume": pos.volume,
            "type": order_type,
            "position": pos.ticket,
            "price": price,
            "deviation": 100,
            "magic": pos.magic,
            "comment": f"Close {expected_comment_prefix}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }
        Print(close_request)

        result = mt5.order_send(close_request)
        if result == None  :
            Print("Open order failed")
            Print(mt5.last_error())
            return None

        log_trade_action(
            "close", pair_name, pos.volume, price,
            "buy" if order_type == mt5.ORDER_TYPE_BUY else "sell",
            pos.sl, pos.tp, f"Close {expected_comment_prefix}",
            pos.ticket, "trade_log.csv", ai_pair_name, video=video
        )

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            Print(f"Failed to close position {pos.ticket}: {result.retcode}", log_path="mt5_errors.txt")
        else:
            Print(f"Closed position {pos.ticket} for {pair_name}", log_path="mt5_errors.txt")


if __name__ == "__main__":
    init()
    positions = mt5.positions_get(symbol = "US100")
    Print(positions)
    recalculate_risk(4.3555,(15,30),"micro_nasdaq",53.75,"MNQ")
    # update_trade("micro_nasdaq","sl",23475,"MNQ")
