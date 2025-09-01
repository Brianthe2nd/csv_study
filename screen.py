# from screeninfo import get_monitors
# for m in get_monitors():
#     Print(str(m))

import mss
import cv2
import numpy as np
from main import Print
from vidgear.gears import CamGear

import cv2
import os

def capture_screen(mon):
    """
    Reads a video path from a text file, retrieves the frame at the current frame number
    from another text file, returns the frame, and increments the frame number by 5.
    If the frame number file does not exist, it will be created with value 0.

    Args:
        video_path_file (str): Path to the text file containing the video file path.
        frame_number_file (str): Path to the text file containing the frame number.

    Returns:
        frame (numpy.ndarray): The retrieved video frame, or None if unable to read.
    """
    # frame_number_file = "frame_number.txt"
    frame_number_file = os.path.join(os.path.dirname(__file__), "frame_number.txt")
    video_path_file = os.path.join(os.path.dirname(__file__),"video_path.txt")
    # 1. Read video path
    if not os.path.exists(video_path_file):
            raise FileNotFoundError(f"Video path file '{video_path_file}' not found.")
    with open(video_path_file, "r") as f:
        video_path = f.read().strip()

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file '{video_path}' not found.")

    # 2. Read or create current frame number
    if not os.path.exists(frame_number_file):
        with open(frame_number_file, "w") as f:
            f.write("0")
        frame_number = 0
    else:
        with open(frame_number_file, "r") as f:
            try:
                frame_number = int(f.read().strip())
            except ValueError:
                raise ValueError("Frame number file does not contain a valid integer.")

    # 3. Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    # Get FPS and frame count
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if fps <= 0:
        raise RuntimeError("Could not retrieve FPS from video.")

    frames_per_5s = int(fps * 5)
    frame_number = frame_number + frames_per_5s

    # Check if the requested frame is beyond the video
    if frame_number >= total_frames:
        cap.release()
        return []

    # 4. Set position
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

    # 5. Read frame
    ret, frame = cap.read()
    cap.release()

    if not ret:
        with open(frame_number_file, "w") as f:
            f.write(str(0))
        return []

    # 6. Increment frame number by 5 seconds worth of frames
    # new_frame_number = frame_number + frames_per_5s

    # 7. Save updated frame number
    with open(frame_number_file, "w") as f:
        f.write(str(frame_number))

    return frame

# def capture_screen(monitor_number=1):
#     with mss.mss() as sct:
        
#         # Get information of monitor 2
#         # monitor_number = 2
#         mon = sct.monitors[monitor_number]

#         # The screen part to capture
#         monitor = {
#             "top": mon["top"],
#             "left": mon["left"],
#             "width": mon["width"],
#             "height": mon["height"],
#             "mon": monitor_number,
#         }
#         # output = "sct-mon{mon}_{top}x{left}_{width}x{height}.png".format(**monitor)

#         # Grab the data
#         # sct_img = sct.grab(monitor)

#         img = np.array(sct.grab(monitor)) # BGR Image
#         # sct_img = sct.grab(monitor)
#         # cv2.imwrite("sct_mon_1.png", img)
#         Print("The image is {} pixels wide and {} pixels high".format(img.shape[1], img.shape[0]))
#         arr = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
        
#         if monitor_number == 2:
#             height , width = arr.shape[:2]
#             arr = arr[15+135:735+135,0:width]
        
#         # cv2.imwrite("ss_tabs_mon_2.png", arr)
        
#         # Save to the picture file
#         # output = "mss_ss.png"
#         # mss.tools.to_png(sct_img.rgb, sct_img.size, output=output)
        
#         # return img
#         # Display the picture
#         # cv2.imshow("OpenCV", arr)
#         # cv2.waitKey(0)

#         return arr

def capture_live_screen(stream_link):
    options = {"STREAM_RESOLUTION": "720p"}
    stream = CamGear(source=stream_link, stream_mode = True, logging=True, **options).start()
    frame = stream.read()
    return frame 
    

if __name__ == "__main__":
    arr = capture_screen(2)  # Change the monitor number as needed
    cv2.imwrite("screen.png",arr)
    # from main import scrape_screen
    # trades = scrape_screen(arr)
    # print("The trades are ")
    # print(trades)