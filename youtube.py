import yt_dlp

def check_stream_is_live(url):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'extract_flat': True,
        'forcejson': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            # Check the 'is_live' flag or 'live_status'
            if info.get('is_live') or info.get('live_status') == 'is_live':
                return True
            else:
                return False
    except yt_dlp.utils.DownloadError as e:
        print(f"[ERROR] yt-dlp failed: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Something went wrong: {e}")
        return False

# cookies_path = 'cookies.txt'
# youtube_url = 'https://www.youtube.com/watch?v=YOUR_STREAM_ID'

# if check_stream_is_live(youtube_url, cookies_path):
#     print("✅ Stream is LIVE!")
# else:
#     print("❌ Stream is NOT live.")


def get_video_title(url):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('title', 'Unknown Title')
    except yt_dlp.utils.DownloadError as e:
        print(f"[ERROR] yt-dlp failed: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Something went wrong: {e}")
        return None

# cookies_path = 'cookies.txt'
# video_url = 'https://www.youtube.com/watch?v=YOUR_VIDEO_ID'

# title = get_video_title(video_url, cookies_path)
# if title:
#     print("🎬 Video title:", title)
# else:
#     print("❌ Failed to retrieve title.")

# import subprocess
# import cv2
# import os
# import numpy as np

# def get_last_frame(video_id , chrome_profile_path="C:/Users/Brayo/AppData/Local/Google/Chrome/User Data/Default"):
#     try:
#         start = time.time()
#         result = subprocess.run(
#             ['yt-dlp', '-f', 'best[height=720]', '-g', video_id],
#             capture_output=True, text=True, check=True
#         )
#         video_url = result.stdout.strip().split('\n')[0]
#         print(video_url)
#         print("Getting video url took:", time.time() - start)

#         # Run ffmpeg to capture a single frame
#         subprocess.run(
#             ['ffmpeg', '-i', video_url, '-vframes', '1', 'last.jpg'],
#             stdout=subprocess.DEVNULL,
#             stderr=subprocess.DEVNULL,
#             check=True
#         )

#         # Read the image
#         frame = cv2.imread('last.jpg')
        
#         # Delete the image file
#         if os.path.exists('last.jpg'):
#             os.remove('last.jpg')
        
#         return frame

#     except subprocess.CalledProcessError as e:
#         print("Subprocess error:", e)
#         return None
#     except Exception as ex:
#         print("Error:", ex)
#         return None
# ffmpeg -i "$(yt-dlp -f "best[height=720]" -g --cookies-from-browser "chrome" [:C:/Users/Brayo/AppData/Local/Google/Chrome/User Data/Default]" 3kdVrCEinvo) -vframes 1 last.jpg

# yt-dlp -f "best[height=720]" -g 3kdVrCEinvo


import cv2
import time
if __name__ == "__main__":
    start  =time.time()
    title = get_video_title("https://www.youtube.com/watch?v=jFtIa_AEFiA")
    frame = check_stream_is_live("https://www.youtube.com/watch?v=jFtIa_AEFiA")
    print("Running this frame took : ",time.time() - start)
    print("Video title is : ",title)
    print("Stream is live : ",frame)
    # cv2.imshow("frame",frame)
    # cv2.waitKey(0)
    