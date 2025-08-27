import pandas as pd

from datetime import datetime, timedelta, timezone

def frame_to_time(fps: float, frame_number: int, start_time: str) -> str:
    """
    Convert a frame number to the corresponding timestamp.

    Args:
        fps (float): Frames per second.
        frame_number (int): Frame index.
        start_time (str): ISO8601 start time string (e.g. "2025-08-22T12:11:46+00:00").

    Returns:
        str: Timestamp in ISO8601 format for the frame.
    """
    # Parse start_time (with timezone awareness)
    start_dt = datetime.fromisoformat(start_time)

    # Calculate seconds elapsed for the frame
    seconds_elapsed = frame_number * fps

    # Add to start datetime
    frame_dt = start_dt + timedelta(seconds=seconds_elapsed)

    # Return as ISO8601 string
    return frame_dt.isoformat()

import re
import ast

def get_trade_type_from_logs(log_text: str, frame_number: int) -> str | None:
    """
    Extracts the trade_type for a given frame number from logs.
    
    Args:
        log_text (str): The full text logs.
        frame_number (int): The frame number to search for.
    
    Returns:
        str | None: The trade_type (e.g., 'buy', 'sell') or None if not found.
    """
    # Split into blocks for each frame
    blocks = re.split(r"-Frame (\d+)-", log_text)
    
    # Blocks come in pairs: frame_number, content
    for i in range(1, len(blocks), 2):
        current_frame = int(blocks[i])
        content = blocks[i + 1]
        
        if current_frame == frame_number:
            # Look for trade dict inside the block
            match = re.search(r"\[{'trade_type':.*?}\]", content, re.DOTALL)
            if match:
                try:
                    trades = ast.literal_eval(match.group(0))
                    if trades and isinstance(trades, list):
                        return trades[0].get("trade_type")
                except Exception:
                    pass
    return None


columns = ["pair", "trader", "event", "timestamp", "yt_time", "link", "screens", "frame", "title"]

trades = pd.read_csv(
    "trades_2_log.csv",
    names=columns,   # give your own headers
    header=None      # tell pandas there's no header row
)
time = "2025-08-22T12:11:46+00:00"
link = "https://www.youtube.com/watch?v=oGJP703ZnQ0"
fps = 0.005596910505401019
trades_arr=[]
for _,row in trades.iterrows():
    if row["event"] == "recalculate_sl" or row["event"] == "update_tp":
        continue
    
    time = frame_to_time(fps,row["frame"],time)
    with open("logs.txt" , "r" , encoding = "utf-8") as file:
        logs = file.read()
    trade_type = get_trade_type_from_logs(logs,row["frame"])
    trade={"pair":row["pair"],"trader":row["trader"],"event":row["event"],"timestamp":time,"trade_type":trade_type}
    trades_arr.append(trade)
    print(trade)

df = pd.DataFrame(trades_arr)
df.to_csv("trades.csv",index=False)

# C:/Users/Brayo/Desktop/TopstepTV_Live_Futures_Day_Trading__Jerome_Powell_&_Economic_Policy_Symposium_Watch_Party!_(8_22_25)
    
    