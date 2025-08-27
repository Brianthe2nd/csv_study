import cv2
from datetime import datetime
import re

def find_frame_by_comment_time(file_path, target_time, target_comment, time_tolerance=10):
    """
    Search a log file for a given comment within a time tolerance
    and return the frame number.

    Args:
        file_path (str): Path to the text log file.
        target_time (str): Target time in "YYYY-MM-DD HH:MM:SS" format.
        target_comment (str): Comment string to match exactly.
        time_tolerance (int): Allowed time difference in seconds.

    Returns:
        int | None: Frame number if found, else None.
    """
    target_dt = datetime.strptime(target_time, "%Y-%m-%d %H:%M:%S")

    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            match = re.match(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+) -Frame (\d+)- (.+)", line)
            if match:
                log_time_str, frame_number, log_data = match.groups()
                log_dt = datetime.strptime(log_time_str, "%Y-%m-%dT%H:%M:%S.%f")

                # Check time difference
                if abs((log_dt - target_dt).total_seconds()) <= time_tolerance:
                    # Check if comment exists in log_data
                    if f"'{target_comment}'" in log_data or f'"{target_comment}"' in log_data:
                        return int(frame_number)

    return None


# Example usage:


def get_frame(video_path, frame_number):
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    success, frame = cap.read()
    cap.release()
    return frame
video_path = "C:/Users/Brayo/Desktop/brian/9_days.mp4"
from name  import get_trader_name
from image_processing import crop_chart_region
from pair_name import get_pair_name 
from main import scrape_screen
from main import detect_chart_layout 
import pandas as pd
from main import get_level_data

trades = pd.read_csv("archive/8_days/trade_log.csv")
print(trades)
# interesting_frames = [175522,181929,304854,407217]

for i,row in trades.iterrows():
    # print(row)
    # comment = row["comment"]
    # time = row["timestamp"]
    # frame_number = find_frame_by_comment_time("archive/8_days/logs.txt", time, comment)
    frame_number = 541764
    # if frame_number in interesting_frames:
    print("Frame number:", frame_number)
    if frame_number is not None:
        or_frame = get_frame(video_path, frame_number)
        frame,logo_exists,total_logos,matches = crop_chart_region(or_frame)
        screen_num,x_divider,y_divider= detect_chart_layout(frame)
        print(f"We have {screen_num} screens")
        # _,_,trades_2_json = get_level_data(screen_2, trades_2,start,stream_mode=stream_mode)
        if logo_exists:
            scaling = matches[0][1][0]
        # frame = crop_chart_region(or_frame)     
        name = get_trader_name(or_frame)
        pair = get_pair_name(frame,scaling)
        trades = scrape_screen(frame,True,logo_scaling=scaling)
        
        print("Trader name: ",name)
        print("Pair: ",pair)
        print("Trades: ",trades)
        print("\n")
        cv2.imshow("frame",or_frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

# from color import process_color

# img = cv2.imread("templates/trade_search.png")
# colors = process_color(img)
# print(colors)