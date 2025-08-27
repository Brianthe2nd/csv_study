import cv2 
import os 
import numpy as np
import time
import concurrent.futures
from std_out import Print
from color import orange_percentage
from config import get_config,update_config



def match_template_or_none(image, template_path, scale):
    if not os.path.exists(template_path):
        return None, []

    template = cv2.imread(template_path)
    if template is None:
        return None, []

    try:
        resized_template = cv2.resize(template, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
    except Exception as e:
        print(f"Resize error at scale {scale}: {e}")
        return None, []

    if resized_template.shape[0] > image.shape[0] or resized_template.shape[1] > image.shape[1]:
        return None, []

    result_match = cv2.matchTemplate(image, resized_template, cv2.TM_CCOEFF_NORMED)
    match_locations = np.where(result_match >= 0.85)
    points = list(zip(match_locations[1], match_locations[0]))  # (x, y)

    match_info = (scale, resized_template.shape[1], resized_template.shape[0])  # (scale, width, height)
    return match_info, points


def check_logo(image, scales=np.linspace(0.3, 2, 50), return_matches=False,
               logo_path="templates/logo.png", custom_image=False):
    """
    Tries to find a logo in the given image at various scales.
    Uses stored scale from config if available, updates config with best scale.
    """
    if not custom_image:
        height, width = image.shape[:2]
        image = image[0:height // 2, 0:width // 2]

    start = time.time()
    all_matches = []

    # Step 1: Try preferred scale first (from config if exists)
    preferred_scale = get_config("logo_scale")
    if preferred_scale is not None:
        match_info, points = match_template_or_none(image, logo_path, preferred_scale)
        if points:
            for pt in points:
                all_matches.append((pt, match_info))
            print(f"✅ Found logo match at preferred scale {preferred_scale}")
        else:
            print(f"⚠ No logo match at preferred scale {preferred_scale}, checking other scales...")

    # Step 2: Try other scales if no matches found
    if not all_matches:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(match_template_or_none, image, logo_path, scale)
                for scale in scales if scale != preferred_scale
            ]
            for future in concurrent.futures.as_completed(futures):
                match_info, points = future.result()
                for pt in points:
                    all_matches.append((pt, match_info))

    # Step 3: Filter duplicates
    filtered_matches = []
    all_matches.sort(key=lambda x: x[1])  # sort by match_info
    for pt, match_info in all_matches:
        if all(abs(pt[0] - fp[0]) >= 8 and abs(pt[1] - fp[1]) >= 8 for fp, _ in filtered_matches):
            filtered_matches.append((pt, match_info))

    end = time.time()
    print("Time taken:", round(end - start, 3), "seconds")

    # Step 4: Save best scale in config & return results
    # print("The filtered matches are:",filtered_matches)
    if filtered_matches:
        best_scale = filtered_matches[0][1][0]  # take scale from first match_info
        update_config("logo_scale", best_scale)

        print(f"🔢 Total distinct logos matched above 0.85: {len(filtered_matches)}")
        print(f"💾 Saved best logo scale {best_scale} to config")
        if return_matches:
            return True, len(filtered_matches), filtered_matches
        else:
            return True, len(filtered_matches)
    else:
        print(f"❌ No good logo match found for {logo_path}")
        if return_matches:
            return False, 0, filtered_matches
        else:
            return False, 0


if __name__ == "__main__":
    image = cv2.imread("names/Screenshot 2025-08-07 154031.png")
    scales = np.linspace(0.3, 2, 50)
    logo_exists, total_matches,matches = check_logo(image,scales,True)
    print("Logo exists:", logo_exists)
    print("Total matches:", total_matches)
    print("Matches:", matches)
    x,y = matches[0][0]
    _,width,height = matches[0][1] 
    
    x_type = (width//3) + width + x
    y_type = height//2 + y
    print("The orange percentage is:",orange_percentage(image[y:y_type,x_type:x_type+width]))
    # cv2.imshow("Detected Logos", image[y:y_type,x_type:x_type+width])
    # cv2.waitKey(0)
    
    