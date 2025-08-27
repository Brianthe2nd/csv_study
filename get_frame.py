import cv2
from name import get_trader_name

def get_frame(video_path, frame_number):
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    success, frame = cap.read()
    cap.release()
    return frame

frames = [427928, 428077, 428226, 428375, 428524, 428673]
if __name__ == "__main__":
    video_path = "C:/Users/Brayo/Desktop/brian/7_days.mp4"
    for frame_number in frames: 
        frame_number =  362815
        frame = get_frame(video_path, frame_number)
        name = get_trader_name(frame)
        print("Trader name:", name)
        cv2.imwrite("frame.jpg", frame)
        cv2.imshow("Frame", frame)
        cv2.waitKey(0)
    