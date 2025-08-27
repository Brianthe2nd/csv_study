import cv2
import numpy as np
# from main import Print
from std_out import Print,play_error_sound,log_exception

def red_percentage(image, lower_red1=(0, 70, 50), upper_red1=(10, 255, 255),
                   lower_red2=(170, 70, 50), upper_red2=(180, 255, 255)):
    """
    Returns the percentage of the image that is red.
    
    Parameters:
        image (np.array): BGR image (as read by cv2).
        lower_red1, upper_red1: Lower and upper HSV bounds for first red range.
        lower_red2, upper_red2: Lower and upper HSV bounds for second red range.

    Returns:
        float: Percentage of red pixels in the image (0 to 100).
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Red can span two ranges in HSV
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)

    red_mask = cv2.bitwise_or(mask1, mask2)
    red_pixels = cv2.countNonZero(red_mask)
    total_pixels = image.shape[0] * image.shape[1]

    percent_red = (red_pixels / total_pixels) * 100
    return percent_red


def orange_percentage(image, lower_orange=(10, 100, 100), upper_orange=(25, 255, 255)):
    """
    Returns the percentage of the image that is orange.

    Parameters:
        image (np.array): BGR image (as read by cv2).
        lower_orange, upper_orange: Lower and upper HSV bounds for orange color.

    Returns:
        float: Percentage of orange pixels in the image (0 to 100).
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Create mask for orange color
    orange_mask = cv2.inRange(hsv, lower_orange, upper_orange)
    orange_pixels = cv2.countNonZero(orange_mask)
    total_pixels = image.shape[0] * image.shape[1]

    percent_orange = (orange_pixels / total_pixels) * 100
    return percent_orange


def gray_percentage(image, lower_gray = (0, 0, 0), upper_gray=(180, 50, 220)):
    """
    Returns the percentage of the image that is gray based on HSV value range.
    
    Parameters:
        image (np.array): BGR image.
        lower_gray, upper_gray: HSV bounds to define gray color.

    Returns:
        float: Percentage of gray pixels.
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    gray_mask = cv2.inRange(hsv, np.array(lower_gray), np.array(upper_gray))
    gray_pixels = cv2.countNonZero(gray_mask)
    total_pixels = image.shape[0] * image.shape[1]
    
    return ((gray_pixels / total_pixels) * 100) + 15

def green_percentage(image, lower_green=(35, 40, 40), upper_green=(85, 255, 255)):
    """
    Returns the percentage of the image that is green.

    Parameters:
        image (np.array): BGR image.
        lower_green, upper_green: HSV bounds for green.

    Returns:
        float: Percentage of green pixels.
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    green_mask = cv2.inRange(hsv, np.array(lower_green), np.array(upper_green))
    green_pixels = cv2.countNonZero(green_mask)
    total_pixels = image.shape[0] * image.shape[1]
    return (green_pixels / total_pixels) * 100

def blue_percentage(image, lower_blue=(100, 150, 50), upper_blue=(130, 255, 255)):
    """
    Returns the percentage of the image that is blue.

    Parameters:
        image (np.array): BGR image (as read by cv2).
        lower_blue, upper_blue: Lower and upper HSV bounds for blue color.

    Returns:
        float: Percentage of blue pixels in the image (0 to 100).
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Create mask for blue color
    blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
    blue_pixels = cv2.countNonZero(blue_mask)
    total_pixels = image.shape[0] * image.shape[1]

    percent_blue = (blue_pixels / total_pixels) * 100
    return percent_blue


def process_color(image):
    """
    Processes the image to calculate the percentage of red, gray, and green colors.

    Parameters:
        image (np.array): BGR image.

    Returns:
        dict: Dictionary with percentages of red, gray, and green.
    """
    return {
        "red": red_percentage(image),
        "gray": gray_percentage(image),
        "green": green_percentage(image)
    }
    

if __name__ == "__main__":
    # Example usage

    image = cv2.imread("trade_x.png")

    import time
    start = time.time()
    red = red_percentage(image)
    gray = gray_percentage(image)
    green = green_percentage(image)
    end = time.time()
    # Print(f"Time taken: {end - start:.2f} seconds")
    # Print(f"Red:  {red:.2f}%")
    # Print(f"Gray: {gray:.2f}%")
    # Print(f"Green:{green:.2f}%")
