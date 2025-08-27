
from std_out import Print,play_error_sound,log_exception

def remove_duplicate_trades(trades):
    unique = []
    seen = set()

    for trade in trades:
        key = tuple(sorted(trade.items()))  # convert dict to hashable form
        if key not in seen:
            seen.add(key)
            unique.append(trade)

    return unique


def classify_trades(color_patterns):
    color_map = {'green': 'G', 'red': 'R', 'gray': 'X'}

    # Convert patterns like "green_red_gray" → "G_R_X"
    pattern_counts = {}
    for key, count in color_patterns.items():
        if count == 0:
            continue
        parts = key.split('_')
        short_key = '_'.join(color_map.get(p, p) for p in parts)
        pattern_counts[short_key] = count

    trades = []

    # Helper: place a trade
    def add_trade(trade_type,status):
        trades.append({"trade_type": trade_type, "sl": False, "tp": False ,"status": status})

    # Helper: update existing trade (first match)
    def update_trade(trade_type, field):
        for trade in trades:
            if trade["trade_type"] == trade_type and not trade[field]:
                trade[field] = True
                return
        # If not found, fallback: add new trade and update
        new_trade = {"trade_type": trade_type, "sl": False, "tp": False}
        new_trade[field] = True
        trades.append(new_trade)

    # --- Process Trades ---

    # 1. Sell in profit → G_R_X
    for _ in range(pattern_counts.get("G_R_X", 0)):
        add_trade("sell","profit")

    # 2. Buy in loss → R_G_X
    for _ in range(pattern_counts.get("R_G_X", 0)):
        add_trade("buy","loss")

    # 3. Buy in profit or TP → G_G_X
    ggx_count = pattern_counts.get("G_G_X", 0)
    for _ in range(ggx_count):
        # If no sell in profit and no buy in loss → it's a TP
        if "G_R_X" not in pattern_counts and "R_G_X" not in pattern_counts:
            update_trade("buy", "tp")
        elif ggx_count > 1 and "G_R_X":
            add_trade("buy","profit")
            update_trade("buy", "tp")


    # 4. SL for either → R_R_X
    rrx_count = pattern_counts.get("R_R_X", 0)
    for _ in range(rrx_count):
        if "R_G_X" in pattern_counts or "G_G_X" in pattern_counts:
            update_trade("buy", "sl")
        elif "G_R_X" in pattern_counts or rrx_count > 1:
            update_trade("sell", "sl")
        elif rrx_count == 1:
            add_trade("sell","loss")
            update_trade("sell", "sl")
        else:
            # update_trade("unknown", "sl")
            pass
    
    trades = remove_duplicate_trades(trades)
    return trades

def classify_trades(color_patterns):
    color_map = {'green': 'G', 'red': 'R', 'gray': 'X'}

    # Convert patterns like "green_red_gray" → "G_R_X"
    pattern_counts = {}
    for key, count in color_patterns.items():
        if count == 0:
            continue
        parts = key.split('_')
        short_key = '_'.join(color_map.get(p, p) for p in parts)
        pattern_counts[short_key] = count

    trades = []

    # Helper: place a trade
    def add_trade(trade_type,status):
        trades.append({"trade_type": trade_type, "sl": False, "tp": False ,"status": status})

    # Helper: update existing trade (first match)
    def update_trade(trade_type, field):
        for trade in trades:
            if trade["trade_type"] == trade_type and not trade[field]:
                trade[field] = True
                return
        # If not found, fallback: add new trade and update
        # new_trade = {"trade_type": trade_type, "sl": False, "tp": False}
        # new_trade[field] = True
        # trades.append(new_trade)

    # --- Process Trades ---
    xxx_count = pattern_counts.get("X_X_X", 0)
    if xxx_count != 0:
        add_trade("limit","profit")
        # trades = remove_duplicate_trades(trades)
        # return trades
    # 1. Sell in profit → G_R_X
    # for _ in range(pattern_counts.get("G_R_X", 0)):
    #     add_trade("sell","profit")
    if "G_R_X" in pattern_counts:
        add_trade("sell","profit")
        if "R_R_X" in pattern_counts:
            update_trade("sell","sl")
        if "G_G_X" in pattern_counts:
            update_trade("sell","tp")
        trades = remove_duplicate_trades(trades)
        return trades
    # 2. Buy in loss → R_G_X
    # for _ in range(pattern_counts.get("R_G_X", 0)):
    #     add_trade("buy","loss")
    if "R_G_X" in pattern_counts:
        add_trade("buy","loss")
        if "R_R_X" in pattern_counts:
            update_trade("buy","sl")
        if "G_G_X" in pattern_counts:
            update_trade("buy","tp")
        
        trades = remove_duplicate_trades(trades)
        return trades

    # 3. Buy in profit or TP → G_G_X
    ggx_count = pattern_counts.get("G_G_X", 0)
    
    if ggx_count == 1:
        add_trade("buy","profit")
        if "R_R_X" in pattern_counts:
            update_trade("buy","sl")
        trades = remove_duplicate_trades(trades)
        return trades
            
    print("GGX count",ggx_count)
    if ggx_count == 2:
        add_trade("buy","profit")
        update_trade("buy","tp")
        if "R_R_X" in pattern_counts:
            update_trade("buy","sl")      
        trades = remove_duplicate_trades(trades)
        return trades 
    

    
    
    # for _ in range(ggx_count):
    #     # If no sell in profit and no buy in loss → it's a TP
    #     if "G_R_X" not in pattern_counts and "R_G_X" not in pattern_counts:
    #         update_trade("buy", "tp")
    #     elif ggx_count > 1 and "G_R_X":
    #         add_trade("buy","profit")
    #         update_trade("buy", "tp")


    # 4. SL for either → R_R_X
    rrx_count = pattern_counts.get("R_R_X", 0)
    if rrx_count == 1:
        add_trade("sell","loss")
        if "G_G_X" in pattern_counts:
            update_trade("sell","tp")
        trades = remove_duplicate_trades(trades)
        return trades 
            

    if rrx_count == 2:
        add_trade("sell","loss")
        update_trade("sell","sl")
        if "G_G_X" in pattern_counts:
            update_trade("buy","tp")  
        trades = remove_duplicate_trades(trades)
        return trades  
    # for _ in range(rrx_count):
    #     if "R_G_X" in pattern_counts or "G_G_X" in pattern_counts:
    #         update_trade("buy", "sl")
    #     elif "G_R_X" in pattern_counts or rrx_count > 1:
    #         update_trade("sell", "sl")
    #     elif rrx_count == 1:
    #         add_trade("sell","loss")
    #         update_trade("sell", "sl")
    #     else:
    #         # update_trade("unknown", "sl")
    #         pass
    
    # trades = remove_duplicate_trades(trades)
    if ggx_count != 0 and rrx_count == 0:
        add_trade("buy","profit")
        trades = remove_duplicate_trades(trades)
        if ggx_count > 1:
            update_trade("buy","tp")  
        if rrx_count > 1:
            update_trade("buy","sl")
            
    if rrx_count != 0 and ggx_count == 0:
        add_trade("sell","loss")
        trades = remove_duplicate_trades(trades)
        if ggx_count > 1:
            update_trade("sell","tp")  
        if rrx_count > 1:
            update_trade("sell","sl")
        return trades
    add_trade("unknown","loss")
    return trades



if __name__ == "__main__":
    # Example usage
    trade_input = {'green_green_gray': 0, 'red_red_gray': 3, 'buy_gray': 1, 'red_green_gray': 2, 'gray_gray_gray': 1, 'sell_gray': 0, 'green_red_gray': 0}
    result = classify_trades(trade_input)
    clean_results = remove_duplicate_trades(result)
    Print(clean_results)
