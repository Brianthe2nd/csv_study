import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timezone

path = "C:/Program Files/FBS MetaTrader 5/terminal64.exe"
def map_symbols(symbol):
    if symbol == "natural_gas":
        return "XNGUSD"
    if symbol == "US500":
        return "US500"
    if symbol == "US100":
        return "US100"



import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timezone


def to_unix(dt_str: str) -> float:
    """
    Convert an ISO 8601 datetime string with timezone to a Unix timestamp.
    
    Args:
        dt_str (str): Example "2025-10-12 08:21:47.950000+00:00"
    
    Returns:
        float: Unix timestamp (can include fractions of a second).
    """
    # dt = datetime.fromisoformat(dt_str)
    return dt_str.timestamp()


def backtest_from_csv(csv_path):
    trades = pd.read_csv(csv_path)

    if not mt5.initialize():
        raise RuntimeError("MetaTrader5 initialization failed")

    results = []
    open_positions = {}

    def get_price(symbol, timestamp):
        """Fetch the close price of the nearest candle after timestamp."""
        # print(type(timestamp))
        print(timestamp)
        timestamp = round(to_unix(timestamp))
        print("The timestamp is:",timestamp)
        rates = mt5.copy_rates_from(symbol, mt5.TIMEFRAME_M1, timestamp, 1)
        print(rates)
        if rates is None or len(rates) == 0:
            return None
        return rates[0]['close']

    for _, row in trades.iterrows():
        symbol = row["pair"]
        symbol = map_symbols(symbol)
        trader = row["trader"]
        event = row["event"]
        timestamp = datetime.fromisoformat(row["timestamp"]).replace(tzinfo=timezone.utc)
        trade_type = row["trade_type"]

        if event == "opened":
            entry_price = get_price(symbol, timestamp)
            if entry_price is None:
                print(f"No entry price for {symbol} at {timestamp}")
                continue
            open_positions[(trader, symbol)] = (entry_price, timestamp, trade_type)

        elif event == "closed" and (trader, symbol) in open_positions:
            exit_price = get_price(symbol, timestamp)
            if exit_price is None:
                print(f"No exit price for {symbol} at {timestamp}")
                continue

            entry_price, entry_time, entry_type = open_positions.pop((trader, symbol))

            # Use entry_type only (ignore 'unknown' on close)
            if entry_type.lower() == "buy":
                pnl = exit_price - entry_price
            elif entry_type.lower() == "sell":
                pnl = entry_price - exit_price
            else:
                pnl = 0.0

            results.append({
                "Trader": trader,
                "Symbol": symbol,
                "Trade Type": entry_type,
                "Entry Price": entry_price,
                "Exit Price": exit_price,
                "Crosscheck": f"Entry: {entry_price}, Exit: {exit_price}",
                "PnL": pnl,
                "Entry Time": entry_time,
                "Exit Time": timestamp
            })

    mt5.shutdown()
    return pd.DataFrame(results)


# Example usage
if __name__ == "__main__":
    df = backtest_from_csv("trades.csv")
    print(df)
    print("Total Return:", df["PnL"].sum())



# Example usage
# if __name__ == "__main__":
#     df = backtest_from_csv("trades.csv")
#     print(df)
#     print("Total Return:", df["PnL"].sum())

12 = 30
780