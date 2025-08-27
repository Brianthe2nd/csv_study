import cv2
import numpy as np
import os

def match_at_scale(image, template, scale):
    try:
        resized_template = cv2.resize(template, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)

        if resized_template.shape[0] > image.shape[0] or resized_template.shape[1] > image.shape[1]:
            return None  # Skip if template is too large

        result = cv2.matchTemplate(image, resized_template, cv2.TM_CCOEFF_NORMED)
        # result = cv2.matchTemplate(image, resized_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, min_loc, max_loc = cv2.minMaxLoc(result)


        return max_val, max_loc, scale
    except Exception as e:
        print(f"Error at scale {scale}: {e}")
        return None


def find_best_scaled_match(image, template_path, scale_range=np.linspace(0.6, 1.1, 500), threshold=0.7):
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return None, None, None

    template = cv2.imread(template_path)
    if template is None:
        print("Failed to load template.")
        return None, None, None

    # Match against full image for now
    height, width = image.shape[:2]
    # image = image[0:height//2, 0:width//2]
    # cv2.imshow("image",image)
    results = []

    for scale in scale_range:
        match = match_at_scale(image, template, scale)
        if match is not None:
            max_val, max_loc, scale = match
            # print(f"Scale: {scale:.2f}, Match: {max_val:.4f}")
            results.append(match)

    # Pick the best result
    if not results:
        print("No valid matches found.")
        return None, None, None

    best = max(results, key=lambda x: x[0])  # max_val
    if best[0] >= threshold:
        return best  # (max_val, max_loc, scale)
    else:
        print("Best match below threshold.")
        return None, None, None


# if __name__ == "__main__":
#     pairs = os.listdir("pairs_2")
    
#     for pair in pairs:
#         pair_path = os.path.join("pairs_2", pair)
#         print(f"\nSearching in: {pair_path}")
#         image = cv2.imread(pair_path)

#         max_val, max_loc, scale = find_best_scaled_match(image, "templates/pair_search.png")
#         x,y = max_loc
#         image_search = cv2.imread("templates/pair_search.png")
#         height,width = image_search.shape[:2]
#         resized_pair = cv2.resize(image,None,fx=1/scale,fy=1/scale,interpolation=cv2.INTER_LINEAR)
#         image_height,image_width = resized_pair.shape[:2]
#         new_image = resized_pair[y+width:image_width , x:x+width]
#         cv2.imshow("Detected Pairs", new_image)
#         cv2.waitKey(0)
#         print("Best match:")
#         print("Value:", max_val)
#         print("Location:", max_loc)
#         print("Scale:", scale)

if __name__ == "__main__":
    pairs = os.listdir("pairs_2")
    
    template_path = "templates/pair_search.png"
    template_img = cv2.imread(template_path)
    template_h, template_w = template_img.shape[:2]
    
    for pair in pairs:
        pair_path = os.path.join("pairs_2", pair)
        print(f"\nSearching in: {pair_path}")
        image = cv2.imread(pair_path)

        result = find_best_scaled_match(image, template_path)
        if result == (None, None, None):
            continue
        
        max_val, max_loc, best_scale = result
        print("Best match:")
        print("Value:", max_val)
        print("Location:", max_loc)
        print("Scale:", best_scale)

        # --- Resize whole pair image so search button fits template exactly ---
        resize_factor = 1.0 / best_scale
        resized_pair = cv2.resize(image, None, fx=resize_factor, fy=resize_factor, interpolation=cv2.INTER_LINEAR)

        # --- Find button location again in resized image (scale=1 now) ---
        result_full = cv2.matchTemplate(resized_pair, template_img, cv2.TM_CCOEFF_NORMED)
        _, _, _, max_loc_new = cv2.minMaxLoc(result_full)
        x, y = max_loc_new

        # --- Crop out search button ---
        pair_no_button = resized_pair.copy()
        height , _ = pair_no_button.shape[:2]
        pair_no_button[y:height, x:x+template_w] = (0, 0, 0)  # Fill with black or transparent
        pair_no_button = pair_no_button[y:height , x+template_w:_]
        # Show both results
        # cv2.imshow("Resized Pair", resized_pair)
        # cv2.imshow("Pair without Search Button", pair_no_button)
        cv2.imwrite("pairs_2_resized/" + pair, pair_no_button)
        # cv2.waitKey(0)
