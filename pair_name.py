import cv2
import numpy as np
import os
import concurrent.futures
# from main import Print
from std_out import Print,play_error_sound,log_exception
from mt5_functions import map_pairs
from math import ceil
from config import get_config,update_config

def match_at_scale(haystack, needle, scale):
    try:
        resized = cv2.resize(needle, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
        iheight, iwidth = resized.shape[:2]
        if resized.shape[0] > haystack.shape[0] or resized.shape[1] > haystack.shape[1]:
            return None
        result_match = cv2.matchTemplate(haystack, resized, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result_match)
        # print("Scale: ",scale," Match: ",max_val)
        return (max_val, scale, max_loc, iwidth, iheight)
    except Exception as e:
        Print(f"Error at scale {scale}: {e}",log_path = "errors.txt")
        
        return None

def get_best_scale(haystack, needle, logo_scaling, preferred_scale=None):
    best_result = (0, 0, (0, 0), 0, 0)  # (max_val, scale, max_loc, width, height)

    # pick start range based on provided scaling
    if logo_scaling < 0.7:
        start = 0.4
    else:
        start = 0.65
    scales = np.linspace(start, 1.7, 40)

    # --- Step 1: try preferred scale from config ---
    preferred_scale = get_config("pair_search_scale")
    pair_logo_accuracy = get_config("pair_search_accuracy")

    if preferred_scale is not None and pair_logo_accuracy is not None:
        result = match_at_scale(haystack, needle, preferred_scale)
        print(f"✅ Preferred pair search scale {preferred_scale} gave an accuracy of {result[0]:.4f} expecting {pair_logo_accuracy:.4f}")
        if result and np.isclose(result[0], pair_logo_accuracy, rtol=1e-2, atol=1e-3):
            best_result = result
            print(f"✅ Preferred pair search scale {preferred_scale} gave expected accuracy {result[0]:.4f}")
        else:
            print(f"⚠ Preferred pair search scale {preferred_scale} failed, checking other scales...")

    # --- Step 2: search other scales if no preferred match or better results exist ---
    if best_result == (0, 0, (0, 0), 0, 0):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(match_at_scale, haystack, needle, scale)
                for scale in scales if scale != preferred_scale
            ]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result and result[0] > best_result[0]:
                    best_result = result

    # --- Step 3: save best scale and accuracy to config ---
    if best_result[0] > 0:
        update_config("pair_search_scale", best_result[1])      # save scale
        update_config("pair_search_accuracy", best_result[0])   # save accuracy
        print(f"💾 Saved best scale={best_result[1]}, accuracy={best_result[0]:.4f}")

    return best_result  # (max_val, best_scale, best_loc, width, height)


def measure_blurriness(image):
    laplacian_var = cv2.Laplacian(image, cv2.CV_64F).var()
    return laplacian_var

def blur_to_level(image, target_blur, step=3):
    blurred = image.copy()
    current_blur = measure_blurriness(blurred)

    while current_blur > target_blur:

        blurred = cv2.GaussianBlur(blurred, (step, step), 0)
        current_blur = measure_blurriness(blurred)

    return blurred

def get_min_bluriness(img):
    pairs = os.listdir("pairs_2_resized")
    min_bluriness = 99999999
    for pair in pairs:
        bluriness = measure_blurriness(cv2.imread("pairs_2_resized/"+pair))
        if bluriness < min_bluriness:
            min_bluriness = bluriness

    nas_bluriness = measure_blurriness(img)
    if nas_bluriness < min_bluriness:
        min_bluriness = nas_bluriness
    
    return min_bluriness



def edges_on_white(img, low_thresh=10, high_thresh=50):
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
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    # if img_gray is None:
    #     raise FileNotFoundError(f"Image not found: {image_path}")

    # Edge detection
    edges = cv2.Canny(img_gray, low_thresh, high_thresh)

    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Create white background
    result = np.ones_like(img_gray) * 255  # white background

    # Draw contours in black
    cv2.drawContours(result, contours, -1, (0, 0, 0), 1)

    return result


def preprocess_with_contours(img):
    # Ensure grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    
    # Threshold to get binary image (invert so text = white)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Create a blank mask
    mask = np.zeros_like(gray)
    
    # Draw all contours (fill)
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        # Optional: filter very small contours (noise)
        if w > 2 and h > 5:
            cv2.drawContours(mask, [cnt], -1, 255, -1)
    
    # Apply mask to original grayscale
    processed = cv2.bitwise_and(gray, gray, mask=mask)
    return processed

def secondary_check(or_cropped,logo_scaling):
    pairs = os.listdir("pairs_2_resized")
    print("SECONDARY CHECK")
    search_button_org = cv2.imread("templates/pair_search.png", cv2.IMREAD_GRAYSCALE)
    max_val, best_scale_for_screen, best_loc,iwidth, iheight = get_best_scale(or_cropped, search_button_org,logo_scaling)
    Print("scaling division:",logo_scaling/best_scale_for_screen)
    Print("best scale:",best_scale_for_screen)
    max_value = 0
    pair_str = ""
    for pair in pairs:
        template_scaled = cv2.imread(f"pairs_2_resized/{pair}", cv2.IMREAD_GRAYSCALE)
        pair_height, pair_width = template_scaled.shape[:2]
        addition = 0
        if pair_height > iheight:
            addition = ceil((pair_height - iheight) / 2)
        h, w = or_cropped.shape[:2]
        cropped = or_cropped[best_loc[1] - addition : best_loc[1] + iheight + addition,best_loc[0] - 2 : best_loc[0] + (iwidth * 5)]


        if template_scaled is None:
            Print(f"Failed to load {pair}")
            continue
        try:
            screen_scaled = cv2.resize(cropped, None, fx=1 / best_scale_for_screen, fy=1 / best_scale_for_screen, interpolation=cv2.INTER_LINEAR)
        except:
            Print(f"Resize failed for {pair}",log_path = "errors.txt")
            
            continue

        if template_scaled.shape[0] > screen_scaled.shape[0] or template_scaled.shape[1] > screen_scaled.shape[1]:
            Print(f"Skipped matching {pair} because scaled template is larger than screen.")
            Print(f"Template is of shape ({template_scaled.shape[0]} , {template_scaled.shape[1]} and screen is of shape {screen_scaled.shape[0] }, {screen_scaled.shape[1]})")
            continue
        screen_scaled = cv2.flip(screen_scaled, 1)
        template_scaled = cv2.flip(template_scaled, 1)
        # cv2.imshow("template",template_scaled)
        # cv2.imshow("screen",screen_scaled)
        # cv2.waitKey(0)
        result_match = cv2.matchTemplate(screen_scaled, template_scaled, cv2.TM_CCOEFF_NORMED)
        _, final_val, _, final_loc = cv2.minMaxLoc(result_match)
        print(f"final val for {pair} is {final_val}")

        
        if final_val > max_value:
            max_value = final_val
            pair_str = pair.split(".")[0]



import cv2
import os
import numpy as np
from math import ceil

def get_pair_name(image, logo_scaling):
    if len(image.shape) == 3 and image.shape[2] == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  

    pairs = os.listdir("pairs_2_resized")
    search_button_org = cv2.imread("templates/pair_search.png", cv2.IMREAD_GRAYSCALE)
    if image is None or search_button_org is None:
        raise ValueError("Failed to load image or search button.")

    height, width = image.shape[:2]
    or_cropped = image[0:height // 2, 0:width // 2]

    # Scale matching
    max_val, best_scale_for_screen, best_loc, iwidth, iheight = get_best_scale(
        or_cropped, search_button_org, logo_scaling
    )
    Print("scaling division:", logo_scaling / best_scale_for_screen)
    Print("best scale:", best_scale_for_screen)

    max_value = 0
    screen_scaled = None
    pair_str = None

    # --- Step 1: Try config first ---
    config_pair_name = get_config("pair_name")
    config_pair_accuracy = get_config("pair_accuracy")

    if config_pair_name and config_pair_accuracy:
        template_scaled = cv2.imread(f"pairs_2_resized/{config_pair_name}.png", cv2.IMREAD_GRAYSCALE)
        if template_scaled is not None:
            pair_height, pair_width = template_scaled.shape[:2]
            addition = max(0, ceil((pair_height - iheight) / 2))

            cropped = or_cropped[
                best_loc[1] - addition : best_loc[1] + iheight + addition,
                best_loc[0] - 2 : best_loc[0] + (iwidth * 5)
            ]

            try:
                screen_scaled = cv2.resize(
                    cropped, None,
                    fx=1 / best_scale_for_screen, fy=1 / best_scale_for_screen,
                    interpolation=cv2.INTER_LINEAR
                )
            except:
                Print(f"Resize failed for {config_pair_name}", log_path="errors.txt")
                screen_scaled = None

            if screen_scaled is not None:
                if not (template_scaled.shape[0] > screen_scaled.shape[0] or 
                        template_scaled.shape[1] > screen_scaled.shape[1]):

                    result_match = cv2.matchTemplate(
                        screen_scaled, template_scaled, cv2.TM_CCOEFF_NORMED
                    )
                    _, final_val, _, _ = cv2.minMaxLoc(result_match)

                    # If accuracy matches cached one, trust config
                    if np.isclose(final_val, float(config_pair_accuracy), rtol=0.01, atol=0.001):
                        Print(f"✅ Using config pair: {config_pair_name} (val={final_val:.3f})")
                        mapped_pair = map_pairs(config_pair_name.split(".")[0])
                        return mapped_pair, screen_scaled, True

    # --- Step 2: Full search over all pairs ---
    for pair in pairs:
        template_scaled = cv2.imread(f"pairs_2_resized/{pair}", cv2.IMREAD_GRAYSCALE)
        if template_scaled is None:
            Print(f"Failed to load {pair}")
            continue

        pair_height, pair_width = template_scaled.shape[:2]
        addition = max(0, ceil((pair_height - iheight) / 2))

        cropped = or_cropped[
            best_loc[1] - addition : best_loc[1] + iheight + addition,
            best_loc[0] - 2 : best_loc[0] + (iwidth * 5)
        ]

        try:
            screen_scaled = cv2.resize(
                cropped, None,
                fx=1 / best_scale_for_screen, fy=1 / best_scale_for_screen,
                interpolation=cv2.INTER_LINEAR
            )
        except:
            Print(f"Resize failed for {pair}", log_path="errors.txt")
            continue

        if (template_scaled.shape[0] > screen_scaled.shape[0] or 
            template_scaled.shape[1] > screen_scaled.shape[1]):
            Print(f"Skipped {pair}, template larger than screen")
            continue

        result_match = cv2.matchTemplate(screen_scaled, template_scaled, cv2.TM_CCOEFF_NORMED)
        _, final_val, _, _ = cv2.minMaxLoc(result_match)
        print(f"final val for {pair} is {final_val}")

        if final_val > max_value:
            max_value = final_val
            pair_str = pair.split(".")[0]

    # --- Step 3: Save best result ---
    if pair_str and max_value > 0.6:
        mapped_pair = map_pairs(pair_str)
        update_config("pair_name", pair_str)
        update_config("pair_accuracy", max_value)
        Print(f"💾 Saved best pair={pair_str}, accuracy={max_value:.3f}")
        return mapped_pair, screen_scaled, True

    return None, screen_scaled, False
    

if __name__ == "__main__":
    import time
    start = time.time()
    image = cv2.imread("pair_test.png", cv2.IMREAD_GRAYSCALE)
    pair = get_pair_name(image)
    Print(pair)
    Print(f"Time taken: {time.time() - start:.2f} seconds")