import platform
import builtins
from datetime import datetime
import subprocess
import traceback
import os

def play_error_sound():
    system = platform.system()

    if system == "Windows":
        import winsound
        winsound.MessageBeep(winsound.MB_ICONHAND)  # Error sound

    elif system == "Darwin":  # macOS
        subprocess.run(["afplay", "/System/Library/Sounds/Funk.aiff"])

    elif system == "Linux":
        # Tries to play a built-in system sound
        subprocess.run(["paplay", "/usr/share/sounds/freedesktop/stereo/dialog-error.oga"])
    else:
        print("Unsupported OS for sound.")

def Print(*args, sep=' ', end='\n', file=None, flush=True ,log_path = "logs.txt"):
    log_path = os.path.join(os.path.dirname(__file__), log_path)
    message = sep.join(map(str, args)) + end
    # frame_number_file = "frame_number.txt"
    frame_number_file = os.path.join(os.path.dirname(__file__), "frame_number.txt")
    try:
        with open(frame_number_file, "r") as f:
                try:
                    frame_number = int(f.read().strip())
                except ValueError:
                    raise ValueError("Frame number file does not contain a valid integer.")
    except :
        frame_number = 0
    
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} -Frame {frame_number}- {message}")
    except PermissionError as e:
        Print(f"PermissionError writing to log: {e}", log_path = os.path.join(os.path.dirname(__file__),"errors.txt"))
        
    if log_path == "mt5_errors.txt":
        try:
            logs_path = os.path.join(os.path.dirname(__file__), "logs.txt")
            with open(logs_path, "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()} - {message}")
        except PermissionError as e:
            Print(f"PermissionError writing to log: {e}", log_path = os.path.join(os.path.dirname(__file__),"errors.txt"))
        

    builtins.print(*args, sep=sep, end=end, file=file, flush=flush)


def log_exception(log_path = "logs.txt"):
    log_path = os.path.join(os.path.dirname(__file__), log_path)
    # Capture the full traceback as a string
    error_text = traceback.format_exc()

    # Write it to the log file
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(error_text + "\n")

    # Also print to console
    Print(error_text,flush= True)
    play_error_sound()