
import os
import cv2
import numpy as np
import json
import threading
import time
import csv
import re


from image_processing import crop_chart_region
from color import process_color
from classify_trades import classify_trades
from pair_name import get_pair_name
from gemini import get_levels
from mt5_functions import recalculate_risk,update_trade,open_trade,close_trade
import traceback
from mt5_functions import map_pairs
from std_out import Print,play_error_sound,log_exception
from logo import check_logo
from name import get_trader_name
from screen import capture_screen
from color import blue_percentage
from border import detect_chart_layout

box_3_x = 0
box_3_y = 1
box_2_x = 2
box_2_y = 3 
box_1_x = 4
box_1_y = 5
box_height = 6
box_width = 7
box_val = 8
CSV_FILE = os.path.join(os.path.dirname(__file__), "trades_2_log.csv")

def reduce_X_close_points_exact(points, threshold=3 ,y_threshold=20):
    reduced = []
    used = [False] * len(points)

    for i, (x1, y1) in enumerate(points):
        if used[i]:
            continue
        
        group = [(x1, y1)]
        # reduced.append((x1, y1))
        used[i] = True

        for j in range(i + 1, len(points)):
            x2, y2 = points[j]
            if not used[j] and abs(x1 - x2) < threshold and abs(y1 - y2) < y_threshold:
                used[j] = True
                group.append((x2, y2))
        leftmost = min(group, key=lambda p: p[0])
        reduced.append(leftmost)

    return reduced

def reduce_Y_close_points_exact(points, threshold=3, x_threshold=20):
    reduced = []
    used = [False] * len(points)

    for i, (x1, y1) in enumerate(points):
        if used[i]:
            continue

        group = [(x1, y1)]
        used[i] = True

        for j in range(i + 1, len(points)):
            x2, y2 = points[j]
            if not used[j] and abs(y1 - y2) < threshold and abs(x1 - x2) < x_threshold:
                group.append((x2, y2))
                used[j] = True

        # Keep only the leftmost point (smallest x)
        leftmost = min(group, key=lambda p: p[0])
        reduced.append(leftmost)

    return reduced


def match_at_scale(image, original_template, scale, mode, threshold, all_points_lock, all_points):
    template = cv2.resize(original_template, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
    h, w = template.shape[:2]

    if h > image.shape[0] or w > image.shape[1]:
        return

    result = cv2.matchTemplate(image, template, mode)
    is_low_better = mode in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]

    if is_low_better:
        locations = np.where(result <= threshold)
    else:
        locations = np.where(result >= threshold)

    scale_points = [(pt[0], pt[1], w, h, scale) for pt in zip(*locations[::-1])]

    # Use lock to safely append to shared list
    with all_points_lock:
        all_points.extend(scale_points)


def match_template_and_draw(image, template_path, threshold=0.9, mode=cv2.TM_CCOEFF_NORMED ,check_x_scale = False):
    
    if not check_x_scale:
        if not os.path.exists(template_path):
            return image, []  # Return original image and no matches

        template = cv2.imread(template_path)
        if template is None:
            return image, []

        h, w = template.shape[:2]
    

        result = cv2.matchTemplate(image, template, mode)

        # Determine matching logic based on mode
        is_low_better = mode in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]
        if is_low_better:
            locations = np.where(result <= threshold)
        else:
            locations = np.where(result >= threshold)

        matches = []
        points=[]
        for pt in zip(*locations[::-1]):  # (x, y)
            x = pt[0]
            y = pt[1]
            points.append((x, y))
        
        points = reduce_X_close_points_exact(points,y_threshold=w/2) 
        points = reduce_Y_close_points_exact(points, x_threshold=w*5)   
        
        for pt in zip(*locations[::-1]):  # (x, y)
            match_val = result[pt[1], pt[0]]
            x= pt[0]
            y= pt[1]
            if (x, y) in points:
                matches.append((x , y , x-w , y , x-3*w , y , match_val))
                # Draw rectangle on the image
                top_left = (x, y)
                bottom_right = (x + w, y + h)
                cv2.rectangle(image, top_left, bottom_right, (0, 255, 0), 1)
            else: 
                continue



        return image, matches,w,h
    else:
        if not os.path.exists(template_path):
            return image, []

        original_template = cv2.imread(template_path)
        if original_template is None:
            return image, []

        matches = []
        all_points = []
        all_points_lock = threading.Lock()
        # check_config
        threads = []
        for scale in np.linspace(0.6, 1.7, 40):
            t = threading.Thread(target=match_at_scale, args=(image, original_template, scale, mode, threshold, all_points_lock, all_points))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        w=0
        h=0
        seen = set()
        unique = []

        for item in all_points:
            key = (item[0], item[1])  # only compare first two values
            if key not in seen:
                seen.add(key)
                unique.append(item)
        all_points =[]
        all_points.extend(unique)
        if all_points:
            raw_points = [(x, y) for x, y, w, h, _ in all_points]
            w = all_points[0][2]
            h = all_points[0][3]
            raw_points = reduce_X_close_points_exact(raw_points, y_threshold=w / 2)
            raw_points = reduce_Y_close_points_exact(raw_points, x_threshold=w * 5)
            for x, y, w, h, val in all_points:
                if (x, y) in raw_points:
                    matches.append((x, y, x - w - 1, y, x - 3 * w, y, h , w, val))


        Print("The number of matches is :", len(matches))
        """update config"""
        return image, matches, w, h if all_points else (image, [], 0, 0)



# --- Main testing code ---

def get_dominant_color_name(color_percentages):
    # Find the color with the highest percentage
    dominant_color = max(color_percentages, key=color_percentages.get)
    if color_percentages[dominant_color] > 50:
        return dominant_color  # e.g., 'red', 'green', or 'gray'
    return None  # No color dominant enough
    

def scrape_screen(image,check_x_scale,logo_scaling):
    
    cropped=image

    matching_modes = [
        cv2.TM_CCOEFF_NORMED
    ]
    
    mode = matching_modes[0]
    # Adjust threshold depending on mode
    if logo_scaling < 0.7:
        start = 0.7
    else :
        start = 0.85
    threshold = 0.15 if mode in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED] else start

    # "config"
    image_with_rects, matches ,w,h = match_template_and_draw(cropped, os.path.join(os.path.dirname(__file__), "templates", "trade_search.png"), threshold=threshold, mode=mode,check_x_scale=check_x_scale)
    converted = [tuple(int(x) if isinstance(x, (np.integer,)) else float(x) for x in item) for item in matches]
    # Assuming 'image', 'converted', 'h', and 'w' are defined earlier in your code.

    avail_trades = []

    # --- Get the dimensions of the main image once before the loop ---
    # This is more efficient than getting it on every iteration.
    img_height, img_width = image.shape[:2]
    # print("There are ",len(converted)," trades")
    for match in converted:
        print("Match:", match)

        # Box 3
        x_3 = match[box_3_x]
        y_3 = match[box_3_y]
        w  = int(match[box_width])
        h  = int(match[box_height])
        if not (0 <= y_3 and y_3 + h <= img_height and 0 <= x_3 and x_3 + w <= img_width):
            print(f"Skipping match due to out-of-bounds coordinates for box 3: {match}")
            continue
        # cv2.rectangle(image, (x_3, y_3), (x_3 + w, y_3 + h), (255, 255, 255), 1)
        # cv2.putText(image, str(match[0]), (x_3, y_3 - 5),
        #             cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
        cropped_region = image[y_3:y_3 + h, x_3:x_3 + w]
        box_3_color = process_color(cropped_region)

        # Box 2
        x_2 = match[box_2_x]
        y_2 = match[box_2_y]
        if not (0 <= y_2 and y_2 + h <= img_height and 0 <= x_2 and x_2 + w <= img_width):
            print(f"Skipping match due to out-of-bounds coordinates for box 2: {match}")
            continue
        # cv2.rectangle(image, (x_2, y_2), (x_2 + w, y_2 + h), (255, 255, 255), 1)
        # cv2.putText(image, str(match[0]), (x_2, y_2 - 5),
        #             cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
        cropped_region = image[y_2:y_2 + h, x_2:x_2 + w]
        box_2_color = process_color(cropped_region)

        # Box 1
        x_1 = match[box_1_x]
        y_1 = match[box_1_y]
        if not (0 <= y_1 and y_1 + h <= img_height and 0 <= x_1 and x_1 + w <= img_width):
            print(f"Skipping match due to out-of-bounds coordinates for box 1: {match}")
            continue
        # cv2.rectangle(image, (x_1, y_1), (x_1 + w, y_1 + h), (255, 255, 255), 1)
        # cv2.putText(image, str(match[0]), (x_1, y_1 - 5),
        #             cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
        cropped_region = image[y_1:y_1 + h, x_1:x_1 + w]
        box_1_color = process_color(cropped_region)
        # print("Box 1 color: ",box_1_color)
        # print("Box 2 color: ",box_2_color)
        # print("Box 3 color: ",box_3_color)
        # print("\n")
        
        # --- Combine and process results ---
        boxes = [box_1_color, box_2_color, box_3_color]

        trade_name = ""
        for i, box in enumerate(boxes, 1):
            result = get_dominant_color_name(box)
            if result is None:
                trade_name = None
                break
            trade_name += "_" + result
            
        if trade_name is None:
            continue
            
        avail_trades.append(trade_name[1:])
        # Print(f"Result:", trade_name[1:])
        # Rest of your processing...

    # cv2.imshow("image",image)
    # cv2.waitKey(4000)
    formatted_trades = {}
    for trade in avail_trades:
        if formatted_trades.get(trade) is None:
            trade_number = avail_trades.count(trade)
            formatted_trades[trade] = trade_number
    
    Print(formatted_trades)
    classified_trades = classify_trades(formatted_trades)
    if classified_trades and classified_trades[0].get("trade_type") == "limit":
        # Move the first element to the end
        classified_trades.append(classified_trades.pop(0))

        
    # cv2.imshow("image",image_with_rects)
    # cv2.waitKey(0)
    return classified_trades

        


        
        # cv2.imshow("Box",cropped_region)
        # cv2.waitKey(0)
        # Print(f"Box 3 Color: {box_3_color}")
        # Print(f"Match: {match}")
    # py_list = matches.tolist()
    # Print("Matches as list:", py_list)

    # cv2.imshow(f"Matches - Mode {mode}", image_with_rects)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    


def save_trade_event(pair, trader, event_type, timestamp, time_s, video_link):
    frame_number_file = os.path.join(os.path.dirname(__file__),"frame_number.txt")
    screen_num_file = os.path.join(os.path.dirname(__file__), "screen_num.txt")
    screen_num = read_file(screen_num_file)
    frame_num = read_file(frame_number_file)
    info_file = os.path.join(os.path.dirname(__file__), "info.json")
    with open(info_file,"r") as file:
        info = json.load(file)
    
    
    video_link = info.get("video_link")
    video_title = info.get("video_title") 
    # frame_num = rea
    with open(CSV_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([pair, trader, event_type, timestamp, time_s, video_link , screen_num , frame_num , video_title])
        
def get_latency_time(mode="normal"):
    latencies = {
        "normal": (15,30),
        "low": (5,15),
        "ultra": (2,5)
    }
    return latencies.get(mode.lower(), "[Unknown mode]")


def get_level_data(frame, trades, start, stream_mode="normal"):
    try:
        trade_json = get_levels(frame, trades)

        # Remove Markdown JSON fences if present
        if trade_json.startswith("```"):
            trade_json = re.sub(r"^```[a-zA-Z0-9]*\s*", "", trade_json)  # remove opening ```
            trade_json = re.sub(r"\s*```$", "", trade_json)              # remove closing ```

        trade_json = trade_json.strip()

        # Debug print (optional)
        Print(trade_json)

        # Parse JSON
        trade_json = json.loads(trade_json)

        time_taken = time.time() - start
        latency = get_latency_time(stream_mode)

        return time_taken, latency, trade_json

    except json.JSONDecodeError as e:
        # Save raw text to json_error.txt
        json_error_path = os.path.join(os.path.dirname(__file__), "json_error.txt")
        with open(json_error_path, "a", encoding="utf-8") as f:
            f.write(trade_json + "\n\n")
        Print(f"Error decoding JSON: {e}", log_path="errors.txt")
        return None

def check_if_level_moving(trade_json,start,stream_mode,crop_screen,check_x_scale,logo_scaling):
    new_frame = capture_screen(2)
    if crop_screen:
        new_frame,logo_exists,total_logos,matches = crop_chart_region(new_frame)
    trades = scrape_screen(new_frame,check_x_scale,logo_scaling)
    time_taken, latency, trade_json_2 = get_level_data(new_frame, trades, start, stream_mode)
    if trade_json_2 == None:
        return True,trade_json
    sl_1 = trade_json.get("sl")
    pair_1 = trade_json.get("pair")
    tp_1 = trade_json.get("tp")
    
    sl_2 = trade_json_2.get("sl")
    pair_2 = trade_json_2.get("pair")
    tp_2 = trade_json_2.get("tp")
    if pair_1 != pair_2:
        Print("pair has finished moving")
        return True,trade_json
    if sl_1 != sl_2 or tp_1 != tp_2:
        Print("level is moving")
        time.sleep(2)
        new_frame = capture_screen(2)
        trades = scrape_screen(new_frame,check_x_scale,logo_scaling)
        time_taken, latency, trade_json = get_level_data(new_frame, trades, start, stream_mode)
        if trade_json == None:
            return True,trade_json_2
        return True,trade_json
    else:
        return True,trade_json


def check_pair_in_only_pairs(trader_id, pair_name, trades_data, trader_config):
    if trader_config.get("only_pairs"):
        if pair_name not in trader_config["only_pairs"]:
            Print(f"[IGNORED] Pair {pair_name} not in allowed list for trader {trader_id}.")
            return False
    
    return True

def check_trader_in_ignore(trader_config,trader_id):
    if trader_config.get("ignore", False):
        Print(f"[IGNORED] Trader {trader_id} is ignored entirely.")
        # return trades_data
        return False
    else :
        return True

def process_trades(pair_name, frame, trades, trades_data, video_link, start, time_s, stream_mode, full_img, crop_screen, name, check_x_scale, scaling ,pair_img,is_micro):
    if not pair_name:
        Print("pair name is none")
        return trades_data

    # Determine trader ID
    if not name:
        """config"""
        trader_id = get_trader_name(full_img)
        if trader_id == "unknown":
            trader_id = "unk" + str(round(scaling, 4))
    else:
        trader_id = name

    current_time = time.time()
    Print("__trades__")
    Print(trades)

    # Ensure trader config exists
    if trader_id not in trades_data:
        trades_data[trader_id] = {
            "active": {},
            "unknown": {},
            "rejected": {},
            "config": {
                "ignore": False,
                "ignore_pairs": [],
                "only_pairs": [],
                "use_custom_risk": False,
                "custom_risk": None
            }
        }

    trader_config = trades_data[trader_id].get("config", {})
    trader_trades = trades_data[trader_id]["active"]
    unknown_signals = trades_data[trader_id]["unknown"]
    reject_trader_trades = trades_data[trader_id]["rejected"]

    # ===== Trader Ignore Check =====
    # if trader_config.get("ignore", False):
    #     Print(f"[IGNORED] Trader {trader_id} is ignored entirely.")
    #     return trades_data

    # # ===== Pair Ignore Check =====
    # if pair_name in trader_config.get("ignore_pairs", []):
    #     Print(f"[IGNORED] Pair {pair_name} ignored for trader {trader_id}.")
    #     return trades_data

    # ===== Pair Whitelist Check =====
    # if trader_config.get("only_pairs"):
    #     if pair_name not in trader_config["only_pairs"]:
    #         Print(f"[IGNORED] Pair {pair_name} not in allowed list for trader {trader_id}.")
    #         return trades_data

    # ===== Check if pair is in only_pairs =====
    if not check_pair_in_only_pairs(trader_id, pair_name, trades_data, trader_config):
        return trades_data
    
    if not check_trader_in_ignore(trader_config,trader_id):
        return trades_data

    if trades:
        trades = trades[0]

        # ===== Handle Unknown Trades =====
        if trades["trade_type"] == "unknown":
            if pair_name in trader_trades:
                trade_key = f"{pair_name}_{trader_trades[pair_name]['trade_type']}"
                unknown_signals[trade_key] = unknown_signals.get(trade_key, 0) + 1
                Print(f"[DEBUG] Unknown signal count for trader {trader_id}, pair {pair_name}: {unknown_signals[trade_key]}")

                if unknown_signals[trade_key] >= 3:
                    trade_data = trader_trades.pop(pair_name)
                    # close_trade(pair_name, pair_name, trader_id=trader_id, video=video_link)
                    Print(f"[CLOSED] {pair_name} ({trades['trade_type']}) closed at {current_time} because the number of unknown signals has reached 3.")
                    save_trade_event(pair_name, trader_id, "closed", current_time, time_s, video_link)
                    unknown_signals[trade_key] = 0

        else:
            # ===== Reset Unknown Signal Count =====
            if pair_name in trader_trades:
                trade_key = f"{pair_name}_{trader_trades[pair_name]['trade_type']}"
                if trade_key in unknown_signals and unknown_signals[trade_key] != 0:
                    Print(f"[RESET] Resetting unknown signal count for trader {trader_id}, pair {pair_name}")
                    unknown_signals[trade_key] = 0

            # ===== New Trade =====
            if pair_name not in trader_trades and pair_name not in reject_trader_trades:

                # Pass custom risk if enabled
                # if trader_config.get("use_custom_risk") and trader_config.get("custom_risk") is not None:
                #     open_trade(pair_name, trades["trade_type"], pair_name, video=video_link, trader_id=trader_id, risk=trader_config["custom_risk"])
                # else:
                #     open_trade(pair_name, trades["trade_type"], pair_name, video=video_link, trader_id=trader_id)

                # time_taken, latency, trade_json = get_level_data(frame, trades, start, stream_mode)
                # if trade_json == None:
                #     Print("Pair confirmation JSON is None ...closing trade")
                #     close_trade(pair_name, pair_name, video=video_link, trader_id=trader_id)
                #     Print(f"[CLOSED] {pair_name} closed at {current_time}")
                #     save_trade_event(pair_name, trader_id, "closed", current_time, time_s, video_link)

                # Validate Pair Name
                # if map_pairs(trade_json["pair"]) != map_pairs(pair_name):
                #     reject_trader_trades[pair_name] = trader_trades.pop(pair_name)
                #     Print(f"The name of the pair does not match. Local: {pair_name}, AI: {trade_json['pair']}")
                #     close_trade(pair_name, pair_name, video=video_link, trader_id=trader_id)
                #     Print(f"[CLOSED] {pair_name} closed at {current_time}")
                #     save_trade_event(pair_name, trader_id, "closed", current_time, time_s, video_link)

                Print("The name of the pair matches")
                trader_trades[pair_name] = {
                    "trade_type": trades["trade_type"],
                    "open_time": current_time,
                    "sl": trades["sl"],
                    "tp": trades["tp"],
                    "status": trades["status"]
                }
                # level_moved = False
                save_trade_event(pair_name, trader_id, "opened", current_time, time_s, video_link)

                # SL check
                if trades["sl"]:
                    # Print("checking if sl is moving")
                    # level_moved, trade_json = check_if_level_moving(trade_json, start, stream_mode, crop_screen, check_x_scale, logo_scaling=scaling)
                    # pip_risk = abs(trade_json["entry_price"] - trade_json["sl_price"])

                    # if trader_config.get("use_custom_risk") and trader_config.get("custom_risk") is not None:
                    #     recalculate_risk(time_taken, latency, pair_name, pip_risk, trade_json["pair"], video=video_link, trader_id=trader_id, risk=trader_config["custom_risk"])
                    # else:
                    #     recalculate_risk(time_taken, latency, pair_name, pip_risk, trade_json["pair"], video=video_link, trader_id=trader_id)
                    save_trade_event(pair_name, trader_id, "recalculate_sl", current_time, time_s, video_link)

                # TP check
                if trades["tp"]:
                    # Print("checking if tp is moving")
                    # if not level_moved:
                    #     level_moved, trade_json = check_if_level_moving(trade_json, start, stream_mode, crop_screen, check_x_scale, logo_scaling=scaling)
                    # update_trade(pair_name, "tp", trade_json["tp_price"], trade_json["pair"], video=video_link, trader_id=trader_id)
                    save_trade_event(pair_name, trader_id, "update_tp", current_time, time_s, video_link)

                Print(f"[OPENED] {pair_name} {trades} at {current_time}")
                

            # ===== Existing Trade Update =====
            elif pair_name in trader_trades:
                level_moved = False
                got_trades = False

                # if (trades["sl"] and not trader_trades[pair_name]["sl"]) or (trades["tp"] and not trader_trades[pair_name]["tp"]):
                #     time_taken, latency, trade_json = get_level_data(frame, trades, start, stream_mode)
                    
                #     if trade_json == None :
                #         pass
                #     got_trades = True

                if trades["sl"] and not trader_trades[pair_name]["sl"]:
                    # Print("checking if sl is moving")
                    # if not got_trades:
                    #     time_taken, latency, trade_json = get_level_data(frame, trades, start, stream_mode)
                    
                    # if trade_json != None:
                    #     pip_risk = abs(trade_json["entry_price"] - trade_json["sl_price"])
                    trader_trades[pair_name]["sl"] = True

                    #     if trader_config.get("use_custom_risk") and trader_config.get("custom_risk") is not None:
                    #         recalculate_risk(time_taken, latency, pair_name, pip_risk, trade_json["pair"], video=video_link, trader_id=trader_id, risk=trader_config["custom_risk"])
                    #     else:
                    #         recalculate_risk(time_taken, latency, pair_name, pip_risk, trade_json["pair"], video=video_link, trader_id=trader_id)
                    # else :
                    #     Print("Skipping trade risk recalculation because trade_json is None",log_path="errors.txt")
                    save_trade_event(pair_name, trader_id, "recalculate_sl", current_time, time_s, video_link)
                if trades["tp"] and not trader_trades[pair_name]["tp"]:
                    # Print("checking if tp is moving")
                    # if not got_trades:
                    #     time_taken, latency, trade_json = get_level_data(frame, trades, start, stream_mode)
                    # if trade_json != None:
                    #     if not level_moved:
                    #         level_moved, trade_json = check_if_level_moving(trade_json, start, stream_mode, crop_screen, check_x_scale, logo_scaling=scaling)
                    trader_trades[pair_name]["tp"] = True
                    #     update_trade(pair_name, "tp", trade_json["tp_price"], trade_json["pair"], video=video_link, trader_id=trader_id)
                    # else:
                    #     Print("Skipping trade TP update because trade_json is None",log_path="errors.txt")
                    save_trade_event(pair_name, trader_id, "update_tp", current_time, time_s, video_link)
                Print(f"[ONGOING] {pair_name} still open")

    else:
        # ===== No Trades — Close If Active =====
        if pair_name in trader_trades:
            trade_data = trader_trades.pop(pair_name)
            Print(trade_data)
            # close_trade(pair_name, pair_name, video=video_link, trader_id=trader_id)
            Print(f"[CLOSED] {pair_name} closed at {current_time}")
            save_trade_event(pair_name, trader_id, "closed", current_time, time_s, video_link)

    return trades_data


def is_paper_acc(matches,image):

    Print("Matches:", matches)
    x,y = matches[0][0]
    _,width,height = matches[0][1] 
    
    x_type = (width//3) + width + x
    y_type = height//2 + y

    # Print("The blue percentage is:",blue_percentage(image[y:y_type,x_type:x_type+width]))
    # cv2.imshow("img",image[y:y_type,x_type:x_type+width])
    # cv2.waitKey(0)
    # cv2.imshow("img",image)
    # cv2.waitKey(0)
    blue_per = blue_percentage(image[y:y_type,x_type:x_type+width])
    Print("The blue percentage is:",blue_per)
    if blue_per != 0:
        if blue_per > 7:
            return True 
    return False

def process_1_screen(frame,check_x_scale,scaling,check_limit_orders,video_link,start,time_s,stream_mode,or_frame,crop_screen,name,trades_data):
    Print("There is 1 screen")
    trades = scrape_screen(frame,check_x_scale,logo_scaling=scaling)
    if check_limit_orders:
        has_limit_order = any(
            trade.get("trade_type") == "limit"
            for trade in trades
        )
        
        if has_limit_order:
            Print("There is a limit order")
        
    Print("trades")
    Print(trades)
    pair_name,pair_img,is_micro = get_pair_name(frame,scaling)
    Print("The pair name is:",pair_name)
    trades_data = process_trades(pair_name=pair_name,frame=frame,trades=trades,trades_data=trades_data,video_link=video_link,start=start,time_s=time_s,stream_mode=stream_mode,full_img=or_frame,crop_screen=crop_screen,name=name,check_x_scale=check_x_scale,scaling=scaling,pair_img=pair_img,is_micro=is_micro)

    return trades_data


def create_or_append_number(filename: str, number: int):
    """
    Creates or overwrites the file so that it always contains exactly one number.
    """
    with open(filename, 'w') as f:  # 'w' clears file before writing
        f.write(str(number) + "\n")



def read_file(filename: str) -> int | None:

    if not os.path.exists(filename):
        return None
    
    with open(filename, 'r') as f:
        lines = f.read().splitlines()
        if not lines:
            return None
        return int(lines[-1])


def process_frame(or_frame,time_s,video_link,trades_data,stream_mode,check_double_screen=True,crop_screen=False,name=False,check_x_scale=False,trader_does_not_have_logo=False,check_paper_acc=True,check_limit_orders=True):
        
        try:
            if crop_screen:
                '''update config'''
                frame,logo_exists,total_logos,matches = crop_chart_region(or_frame)
                if logo_exists:
                    scaling = matches[0][1][0]
                # Print(scaling)
            else:
                frame = or_frame
                logo_exists, total_logos ,matches = check_logo(frame,return_matches=True)
                if logo_exists:
                    scaling = matches[0][1][0]
            

            # Print("The logos are :")
            # Print(matches)
            if trader_does_not_have_logo:
                logo_exists = True  
                scaling = "none"
                frame = or_frame
                total_logos = 1    
                      
            if logo_exists:
                if total_logos > 1:
                    Print("There is more than one logo",log_path="errors.txt")
                    return trades_data
                if check_paper_acc and trader_does_not_have_logo == False:
                    if is_paper_acc(matches,or_frame):
                        return trades_data
                start = time.time()
                if check_double_screen:
                    screen_num,x_divider,y_divider= detect_chart_layout(frame)
                    Print(f"The screen number is ,{screen_num}")
                else:
                   screen_num = 1
                
                screen_num_file = os.path.join(os.path.dirname(__file__), "screen_num.txt")
                create_or_append_number(screen_num_file,screen_num)
                
                if True:
                    trades_data = process_1_screen(frame=frame,check_x_scale=check_x_scale,scaling=scaling,video_link=video_link,start=start,time_s=time_s,check_limit_orders=check_limit_orders,stream_mode=stream_mode,or_frame=or_frame,crop_screen=crop_screen,name=name,trades_data=trades_data)

                elif screen_num == 2:
                    Print("There are 2 screens")
                    border = int(x_divider[0])
                    frame_height ,frame_width = frame.shape[:2]
                    first_image = frame[0:frame_height,0:border]
                    second_image = frame[0:frame_height,border:frame_width]
                    trades = scrape_screen(first_image,check_x_scale,logo_scaling=scaling)
                    if check_limit_orders:
                        has_limit_order = any(
                            trade.get("trade_type") == "limit"
                            for trade in trades
                        )
                        
                        if has_limit_order:
                            Print("There is a limit order")
                    # cv2.imshow("first",first_image)
                    # cv2.imshow("second",second_image)
                    # cv2.imwrite("first.png",first_image)
                    # cv2.imwrite("second.png",second_image)
                    # cv2.waitKey(0)
                    
                    pair_name = get_pair_name(first_image,scaling)
                    Print("Pair name from first image",pair_name)
                    Print("trades from first image")
                    Print(trades)
                    trades_2 = scrape_screen(second_image,check_x_scale,logo_scaling=scaling)
                    if check_limit_orders:
                        has_limit_order = any(
                            trade.get("trade_type") == "limit"
                            for trade in trades_2
                        )
                        
                        if has_limit_order:
                            Print("There is a limit order")
                    Print("trades from second image")
                    Print(trades_2)
                    _,_,trade_json_2 = get_level_data(second_image, trades_2,0,stream_mode)
                    if trade_json_2 == None:
                        Print(f"Could not process screen 2 of {screen_num} because trade_json is None",log_path="errors.txt")
                        trades_data = process_1_screen(frame,check_x_scale,scaling,check_limit_orders,video_link,start,time_s,stream_mode,or_frame,crop_screen,name,trades_data=trades_data)
                    else:
                        Print("THE TRADE JSON IS ")
                        # from pPrint import pPrint
                        Print(trade_json_2)
                        
                        pair_name_2 = trade_json_2.get("pair")
                        pair_name_2 = map_pairs(pair_name_2)
                        if pair_name != None and pair_name_2 != None:           
                            
                            if map_pairs(pair_name) == map_pairs(pair_name_2):
                                """combine trades"""
                                trades_1 = trades[0]
                                trades_2 = trades_2[0]
                                if trades_1 != trades_2:
                                    if trades_1["trade_type"] == trades_2["trade_type"]:
                                        trades = trades_1

                                        trades["sl"] = trades_1["sl"] or trades_2["sl"]
                                        trades["tp"] = trades_1["tp"] or trades_2["tp"]
                                        trades["pair"] = pair_name
                                        trades["status"] = trades_1["status"]
                                        trades_arr=[]
                                        trades_arr.append(trades)
                                        
                                        
                                        trades_data = process_trades(pair_name=pair_name,frame=frame,trades=trades_arr,trades_data=trades_data,video_link=video_link,start=start,time_s=time_s,stream_mode=stream_mode,full_img=or_frame,crop_screen=crop_screen,name=name,check_x_scale=check_x_scale,scaling=scaling)
                                else :
                                    trades_data = process_trades(pair_name=pair_name,frame=frame,trades=trades,trades_data=trades_data,video_link=video_link,start=start,time_s=time_s,stream_mode=stream_mode,full_img=or_frame,crop_screen=crop_screen,name=name,check_x_scale=check_x_scale,scaling=scaling)
                            else:
                                trades_data = process_trades(pair_name=pair_name,frame=frame,trades=trades,trades_data=trades_data,video_link=video_link,start=start,time_s=time_s,stream_mode=stream_mode,full_img=or_frame,crop_screen=crop_screen,name=name,check_x_scale=check_x_scale,scaling=scaling)
                                trades_data = process_trades(pair_name=pair_name_2,frame=frame,trades=trades_2,trades_data=trades_data,video_link=video_link,start=start,time_s=time_s,stream_mode=stream_mode,full_img=or_frame,crop_screen=crop_screen,name=name,check_x_scale=check_x_scale,scaling=scaling)
                        else:
                            trades_data = process_trades(pair_name=pair_name,frame=frame,trades=trades,trades_data=trades_data,video_link=video_link,start=start,time_s=time_s,stream_mode=stream_mode,full_img=or_frame,crop_screen=crop_screen,name=name,check_x_scale=check_x_scale,scaling=scaling)
                            trades_data = process_trades(pair_name=pair_name_2,frame=frame,trades=trades_2,trades_data=trades_data,video_link=video_link,start=start,time_s=time_s,stream_mode=stream_mode,full_img=or_frame,crop_screen=crop_screen,name=name,check_x_scale=check_x_scale,scaling=scaling)
                        
                        
                elif screen_num == 3:
                    print("We have 3 screens")
                    trades = scrape_screen(frame,check_x_scale,logo_scaling=scaling)
                    if check_limit_orders:
                        has_limit_order = any(
                            trade.get("trade_type") == "limit"
                            for trade in trades
                        )
                        
                        if has_limit_order:
                            Print("There is a limit order")
                    Print("trades")
                    Print(trades)
                    pair_name = get_pair_name(frame,scaling)
                    Print("The pair name is:",pair_name)
                    trades_data = process_trades(pair_name=pair_name,frame=frame,trades=trades,trades_data=trades_data,video_link=video_link,start=start,time_s=time_s,stream_mode=stream_mode,full_img=or_frame,crop_screen=crop_screen,name=name,check_x_scale=check_x_scale,scaling=scaling)
                elif screen_num == 4:
                    Print("We have 4 screens")
                    x_div = int(x_divider[0])
                    y_div = int(y_divider[0])
                    frame_height ,frame_width = frame.shape[:2]
                    screen_1 = frame[0:y_div,0:x_div]
                    screen_2 = frame[0:y_div,x_div:frame_width]
                    screen_3 = frame[y_div:frame_height,0:x_div]
                    screen_4 = frame[y_div:frame_height,x_div:frame_width]
                    
                    trades_1 = scrape_screen(screen_1,check_x_scale,logo_scaling=scaling)
                    if check_limit_orders:
                        has_limit_order = any(
                            trade.get("trade_type") == "limit"
                            for trade in trades_1
                        )
                        
                        if has_limit_order:
                            Print("There is a limit order")
                    _,_,trades_1_json = get_level_data(screen_1, trades_1,start,stream_mode=stream_mode)
                    if trades_1_json == None:
                        Print(f"Could not process screen 1 of {screen_num} because trade_json is None",log_path="errors.txt")
                        trades_data = process_1_screen(frame,check_x_scale,scaling,check_limit_orders,video_link,start,time_s,stream_mode,or_frame,crop_screen,name,trades_data) 
                    else:
                        screen_1_pair = trades_1_json.get("pair")
                        screen_1_pair = map_pairs(screen_1_pair)
                        trades_data = process_trades(pair_name=screen_1_pair,frame=screen_1,trades=trades_1,trades_data=trades_data,video_link=video_link,start=start,time_s=time_s,stream_mode=stream_mode,full_img=or_frame,crop_screen=crop_screen,name=name,check_x_scale=check_x_scale,scaling=scaling)
                        # trades_2_json = get_levels(screen_2, trades_2)
                        trades_2 = scrape_screen(screen_2,check_x_scale,logo_scaling=scaling)
                        if check_limit_orders:
                            has_limit_order = any(
                                trade.get("trade_type") == "limit"
                                for trade in trades_2
                            )
                            
                            if has_limit_order:
                                Print("There is a limit order")
                        _,_,trades_2_json = get_level_data(screen_2, trades_2,start,stream_mode=stream_mode)
                        if trades_2_json == None:
                            Print(f"Could not process screen 2 of {screen_num} because trade_json is None",log_path="errors.txt")
                            trades_data = process_1_screen(frame,check_x_scale,scaling,check_limit_orders,video_link,start,time_s,stream_mode,or_frame,crop_screen,name,trades_data)
                        
                        else:
                            screen_2_pair = trades_2_json.get("pair")
                            screen_2_pair = map_pairs(screen_2_pair)
                            trades_data = process_trades(pair_name=screen_2_pair,frame=screen_2,trades=trades_2,trades_data=trades_data,video_link=video_link,start=start,time_s=time_s,stream_mode=stream_mode,full_img=or_frame,crop_screen=crop_screen,name=name,check_x_scale=check_x_scale,scaling=scaling)

                            trades_3 = scrape_screen(screen_3,check_x_scale,logo_scaling=scaling)
                            if check_limit_orders:
                                has_limit_order = any(
                                    trade.get("trade_type") == "limit"
                                    for trade in trades_3
                                )
                                
                                if has_limit_order:
                                    Print("There is a limit order")
                            _,_,trades_3_json = get_level_data(screen_3, trades_3,start,stream_mode=stream_mode)
                            if trades_3_json == None:
                                Print(f"Could not process screen 3 of {screen_num} because trade_json is None",log_path="errors.txt")
                                trades_data = process_1_screen(frame,check_x_scale,scaling,check_limit_orders,video_link,start,time_s,stream_mode,or_frame,crop_screen,name,trades_data)
                            
                            else:    
                                screen_3_pair = trades_3_json.get("pair")
                                screen_3_pair = map_pairs(screen_3_pair)
                                trades_data = process_trades(pair_name=screen_3_pair,frame=screen_3,trades=trades_3,trades_data=trades_data,video_link=video_link,start=start,time_s=time_s,stream_mode=stream_mode,full_img=or_frame,crop_screen=crop_screen,name=name,check_x_scale=check_x_scale,scaling=scaling)
                                    
                                trades_4 = scrape_screen(screen_4,check_x_scale,logo_scaling=scaling)
                                if check_limit_orders:
                                    has_limit_order = any(
                                        trade.get("trade_type") == "limit"
                                        for trade in trades_4
                                    )
                                    
                                    if has_limit_order:
                                        Print("There is a limit order")
                                _,_,trades_4_json = get_level_data(screen_4, trades_4,start,stream_mode=stream_mode)
                                if trades_4_json == None:
                                    Print(f"Could not process screen 4 of {screen_num} because trade_json is None",log_path="errors.txt")
                                    trades_data = process_1_screen(frame,check_x_scale,scaling,check_limit_orders,video_link,start,time_s,stream_mode,or_frame,crop_screen,name,trades_data)
                                else:
                                    screen_4_pair = trades_4_json.get("pair")
                                    screen_4_pair = map_pairs(screen_4_pair)
                                    trades_data = process_trades(pair_name=screen_4_pair,frame=screen_4,trades=trades_4,trades_data=trades_data,video_link=video_link,start=start,time_s=time_s,stream_mode=stream_mode,full_img=or_frame,crop_screen=crop_screen,name=name,check_x_scale=check_x_scale,scaling=scaling)
                            
            else:
                Print("No logo found")
                return trades_data
                    

            return trades_data

        except Exception as e:
            Print(f"[ERROR in main] {e}",log_path = os.path.join(os.path.dirname(__file__),"errors.txt"))
            log_exception(log_path = os.path.join(os.path.dirname(__file__),"errors.txt"))
            return trades_data


if __name__ == "__main__":
    img = cv2.imread("screen.png")
    logo_scaling = 1
    trades = scrape_screen(img,check_x_scale=False,logo_scaling=logo_scaling)
    # check_limit_orders = True
    # if check_limit_orders:
    #     has_limit_order = any(
    #         trade.get("trade_type") == "limit"
    #         for trade in trades
    #     )
        
    #     if has_limit_order:
    #         Print("There is a limit order")
    # Print("trades")
    Print(trades)