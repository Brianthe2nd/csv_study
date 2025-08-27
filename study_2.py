import cv2
import numpy as np

def edges_on_white(image_path, low_thresh=10, high_thresh=50):
    """
    Reads an image, finds edges, draws contours on a white background, and returns the result.

    Parameters:
        image_path (str): Path to the input image.
        low_thresh (int): Lower threshold for Canny edge detection.
        high_thresh (int): Upper threshold for Canny edge detection.

    Returns:
        result (numpy.ndarray): White background with drawn contours.
    """

    # Read image in grayscale
    img_gray = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img_gray is None:
        raise FileNotFoundError(f"Image not found: {image_path}")

    # Edge detection
    edges = cv2.Canny(img_gray, low_thresh, high_thresh)

    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Create white background
    result = np.ones_like(img_gray) * 255  # white background

    # Draw contours in black
    cv2.drawContours(result, contours, -1, (0, 0, 0), 1)

    return result

# Example usage:
output_img = edges_on_white("pairs_2_resized/crude_oil.png")
cv2.imshow("Contours on White", output_img)
cv2.waitKey(0)
cv2.destroyAllWindows()
