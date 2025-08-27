import re

# The raw log data provided by the user.
# In a real-world scenario, you would read this from a file, e.g.,
with open('C:/Users/Brayo/Desktop/dakota_floor/archive/2_days/errors.txt', 'r' , encoding='utf-8') as f:
    log_data = f.read()
# log_data = """
# 2025-08-08T22:22:15.865793 - [ERROR in main] OpenCV(4.11.0) D:\\a\\opencv-python\\opencv-python\\opencv\\modules\\imgproc\\src\\color.cpp:199: error: (-215:Assertion failed) !_src.empty() in function 'cv::cvtColor'

# Traceback (most recent call last):
#   File "C:\\Users\\Brayo\\Desktop\\dakota_floor\\main.py", line 664, in process_frame
#     trades = scrape_screen(frame,check_x_scale)
#   File "C:\\Users\\Brayo\\Desktop\\dakota_floor\\main.py", line 349, in scrape_screen
#     box_2_color = process_color(cropped_region)
#   File "C:\\Users\\Brayo\\Desktop\\dakota_floor\\color.py", line 122, in process_color
#     "red": red_percentage(image),
#            ~~~~~~~~~~~~~~^^^^^^^
#   File "C:\\Users\\Brayo\\Desktop\\dakota_floor\\color.py", line 19, in red_percentage
#     hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
# cv2.error: OpenCV(4.11.0) D:\\a\\opencv-python\\opencv-python\\opencv\\modules\\imgproc\\src\\color.cpp:199: error: (-215:Assertion failed) !_src.empty() in function 'cv::cvtColor'


# 2025-08-08T22:32:18.177679 - [ERROR in main] OpenCV(4.11.0) D:\\a\\opencv-python\\opencv-python\\opencv\\modules\\imgproc\\src\\color.cpp:199: error: (-215:Assertion failed) !_src.empty() in function 'cv::cvtColor'

# Traceback (most recent call last):
#   File "C:\\Users\\Brayo\\Desktop\\dakota_floor\\main.py", line 664, in process_frame
#     trades = scrape_screen(frame,check_x_scale)
#   File "C:\\Users\\Brayo\\Desktop\\dakota_floor\\main.py", line 349, in scrape_screen
#     box_2_color = process_color(cropped_region)
#   File "C:\\Users\\Brayo\\Desktop\\dakota_floor\\color.py", line 122, in process_color
#     "red": red_percentage(image),
#            ~~~~~~~~~~~~~~^^^^^^^
#   File "C:\\Users\\Brayo\\Desktop\\dakota_floor\\color.py", line 19, in red_percentage
#     hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
# cv2.error: OpenCV(4.11.0) D:\\a\\opencv-python\\opencv-python\\opencv\\modules\\imgproc\\src\\color.cpp:199: error: (-215:Assertion failed) !_src.empty() in function 'cv::cvtColor'
# """

def filter_unique_errors(logs):
    """
    Filters unique errors from log data.

    Args:
        logs (str): A string containing the full log data.

    Returns:
        list: A list of strings, where each string is a unique error block.
    """
    # Use a regex to split the log data into individual error entries.
    # This pattern looks for the timestamp that starts each log entry.
    error_entries = re.split(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}\s-\s)', logs)
    
    unique_errors = set()
    processed_errors = []

    # Reconstruct the full error messages
    full_entries = []
    for i in range(1, len(error_entries), 2):
        # Combine the timestamp with its corresponding message
        if i + 1 < len(error_entries):
            full_entries.append(error_entries[i] + error_entries[i+1])

    for entry in full_entries:
        if entry.strip():
            # The "unique" part of the error is the traceback and the final error line.
            # We can remove the timestamp to compare errors.
            error_signature = re.sub(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}\s-\s', '', entry).strip()
            
            if error_signature not in unique_errors:
                unique_errors.add(error_signature)
                processed_errors.append(entry.strip())
                
    return processed_errors

# --- Main Execution ---
if __name__ == "__main__":
    unique_error_list = filter_unique_errors(log_data)
    
    output_filename = "unique_errors.txt"
    print("There are {len(unique_error_list)} unique error(s).")
    with open(output_filename, "w",encoding="utf-8") as f:
        for error in unique_error_list:
            f.write(error + "\n\n")
            
    print(f"Successfully filtered {len(unique_error_list)} unique error(s).")
    print(f"Output saved to '{output_filename}'")

