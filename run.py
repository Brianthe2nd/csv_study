
from main import process_frame,create_or_append_number
from mt5_functions import init
from screen import capture_screen,capture_live_screen
import json
import os
import time
import csv
from std_out import Print
import random
from send_data import send_zipped_file,collect_and_zip_files
import sys
import shutil
import traceback
from datetime import datetime





def init_trades_log():
    # CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
    CSV_FILE = os.path.join(os.path.dirname(__file__), "trades_2_log.csv")
    # # Ensure CSV file has a header if it doesn't exist
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['pair', 'trader', 'event', 'timestamp' ,'yt_time','link','screens','frame','title'])




def create_data():
    trades_data = {
        "example": {
            "active": {
                random.choice(["GBPUSD", "USDJPY"]): {
                    "trade_type": random.choice(["buy", "sell"]),
                    "open_time": time.time(),
                    "sl": True,
                    "tp": True,
                    "status": "open"
                }
            },
            "unknown": {},
            "rejected": {},
            "config": {
                "ignore": True,
                "ignore_pairs": ["EURUSD"],
                "only_pairs": ["GBPUSD", "USDJPY"],
                "use_custom_risk": True,
                "custom_risk": 0.02
            }
        },
        "jd": {
            "active": {},
            "unknown": {},
            "rejected": {},
            "config": {
                "ignore": False,
                "ignore_pairs": [],
                "only_pairs": [],
                "use_custom_risk": True,
                "custom_risk": 0.2
            }
        },
        "doom": {
            "active": {},
            "unknown": {},
            "rejected": {},
            "config": {
                "ignore": False,
                "ignore_pairs": [],
                "only_pairs": ["US100"],
                "use_custom_risk": False,
                "custom_risk": 0
            }
        }
    }
    trades_data_file = os.path.join(os.path.dirname(__file__),"trades_data.json")
    with open(trades_data_file, "w") as f:
        json.dump(trades_data, f, indent=4)

# Example usage
# create_data()


def main():
    video_path_file = os.path.join(os.path.dirname(__file__),"video_path.txt")
    try:
        video_files = [f for f in os.listdir(os.path.dirname(__file__)) if f.endswith((".mp4", ".mkv", ".webm"))]
        if not video_files:
            raise FileNotFoundError("No video found in the csv_study folder")
        
        if not os.path.exists(video_path_file):
            with open(video_path_file, "w") as f:
                f.write(os.path.join(os.path.dirname(__file__),video_files[0]))

        # init(path)
        stream_is_live = True
        stream_link = ""
        stream_name = ""
        time_s = 0
        stream_mode = "low"
        active_trades = {}
        path = "C:/Program Files/FBS MetaTrader 5/terminal64.exe"
        # path = "C:/Program Files/MetaTrader 5/terminal64.exe"
        check_double_screen =  True
        crop_screen = True
        name = False
        check_x_scale = True
        """for when the x scale is changing in size"""
        trader_does_not_have_logo = False
        check_paper_acc = True
        check_limit_orders = False
        create_new_trade_data_file = True
        info_file = os.path.join(os.path.dirname(__file__), "info.json")
        with open(info_file,"r") as file:
            info = json.load(file)
            
        name = info.get("video_name").lower()
        if "jay" in name:
            name = "Jay"
            crop_screen = False
        elif "dee" in name:
            name = "Dee"
            crop_screen = False
        elif "aaron" in name:
            name = "Aaron"
            crop_screen = False
        elif "dakota" in name:
            name = "Dakota"
            crop_screen = False
        elif "anne" in name:
            name = "Marie"
            crop_screen = False
        

        # Start Wi-Fi monitor in background
        # start_wifi_thread("itel P55 5G")

        # Single JSON file for all trades
        if create_new_trade_data_file:
            create_data()
        trades_file = os.path.join(os.path.dirname(__file__),"trades_data.json")

        if not os.path.exists(trades_file):
            with open(trades_file, "w") as f:
                json.dump({}, f)

        count = 2
        while True:
            # internet_available.wait()  # Block here if no internet

            if stream_is_live:
                start=time.time()
                image = capture_screen(count)
                screen_num_file = os.path.join(os.path.dirname(__file__), "screen_num.txt")
                create_or_append_number(screen_num_file,0)
                
                # cv2.imshow("image", image)
                # cv2.waitKey(3000)
                if len(image) == 0:
                    break

                try:
                    with open(trades_file, "r") as f:
                        trades_data = json.load(f)
                except json.JSONDecodeError:
                    trades_data = {}

                trades_data = process_frame(
                    image,
                    time_s=time_s,
                    video_link=stream_name,
                    trades_data=trades_data,  # pass single dict
                    stream_mode=stream_mode,
                    check_double_screen=check_double_screen,
                    crop_screen=crop_screen,
                    name=name,
                    check_x_scale=check_x_scale,
                    check_paper_acc=check_paper_acc,
                    check_limit_orders=check_limit_orders
                )

                # Save updated data back to single JSON file
                with open(trades_file, "w") as f:
                    json.dump(trades_data, f, indent=2)
                print("Processing this image took: ",time.time()-start)
                print("\n")
        
        # 1. Read video path
        video_path_file = os.path.join(os.path.dirname(__file__),"video_path.txt")
        if not os.path.exists(video_path_file):
                raise FileNotFoundError(f"Video path file '{video_path_file}' not found.")
        with open(video_path_file, "r") as f:
            video_path = f.read().strip()
        delete_file(video_path)
        folder, zip_file = collect_and_zip_files()
        Print("saved the zip file in: ",zip_file)
        send_zipped_file(local_zip=zip_file)
        video_path_file = os.path.join(os.path.dirname(__file__),"video_path.txt")
    except Exception as e:
        print(e)
        traceback.print_exc()
        if not os.path.exists(video_path_file):
            raise FileNotFoundError(f"Video path file '{video_path_file}' not found.")
        with open(video_path_file, "r") as f:
            video_path = f.read().strip()
        delete_file(video_path)




def delete_file(file_path: str) -> bool:
    """
    Deletes a file if it exists.

    Args:
        file_path (str): Path to the file to be deleted.

    Returns:
        bool: True if the file was deleted, False if it didn't exist.
    """
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"[DELETED] {file_path}")
            return True
        except Exception as e:
            print(f"[ERROR] Could not delete {file_path}: {e}")
            return False
    else:
        print(f"[SKIPPED] {file_path} does not exist.")
        return False


def archive_trade_logs(video_path_file):
    """
    Creates a folder and moves specific trade log files into it,
    then deletes them from the current folder (via move).

    Args:
        destination_root (str): Base directory where the archive folder will be created.
    """
    # List of files to archive
    files_to_move = [
        os.path.join(os.path.dirname(__file__),"trade_log.csv"),
        os.path.join(os.path.dirname(__file__),"trades_2_log.csv"),
        os.path.join(os.path.dirname(__file__),"logs.txt"),
        os.path.join(os.path.dirname(__file__),"mt5_errors.txt"),
        os.path.join(os.path.dirname(__file__),"active_trades.json"),
        os.path.join(os.path.dirname(__file__),"errors.txt")
    ]

    # Create destination folder with timestamp
    # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_folder = video_path_file.split("/")[-1].split(".")[0]
    dest_folder = os.path.join(os.path.dirname(__file__),"archive",dest_folder)
    os.makedirs(dest_folder, exist_ok=True)

    # Move files if they exist
    for filename in files_to_move:
        if os.path.exists(filename):
            shutil.move(filename, os.path.join(dest_folder, filename))
            print(f"[MOVED] {filename} -> {dest_folder}")
        else:
            print(f"[SKIPPED] {filename} not found.")

    print(f"Archive completed: {dest_folder}")



if __name__ == "__main__":
    video = sys.argv[1]  # full path passed in from subprocess
    main()
