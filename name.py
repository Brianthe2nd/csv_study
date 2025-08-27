import cv2
import os
import numpy as np
import fnmatch
from concurrent.futures import ThreadPoolExecutor, as_completed
from std_out import Print
from config import get_config,update_config

def match_template_with_best(image, template_path, threshold=0.95):
    """Original single-size match."""
    if not os.path.exists(template_path):
        return None, 0.0

    template = cv2.imread(template_path)
    if template is None:
        return None, 0.0

    result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    return (max_loc, max_val) if max_val > threshold else (None, max_val)


def match_template_resized(image, template_path, threshold=0.85):
    """Slower method: resize template from 0.65 to 1.75 scale."""
    template = cv2.imread(template_path)
    if template is None:
        return None, 0.0

    for scale in np.linspace(0.65, 1.75, num=12):
        if scale == 1.0:
            continue

        new_w = int(template.shape[1] * scale)
        new_h = int(template.shape[0] * scale)
        if new_w < 5 or new_h < 5:
            continue

        resized_template = cv2.resize(template, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        result = cv2.matchTemplate(image, resized_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val > threshold:
            return max_loc, max_val,scale

    return None, 0.0, 0.0


# === Unified worker functions ===
def process_original(name, cropped, threshold):
    """Try matching at original size."""
    template_path = os.path.join('names', name)
    match, val = match_template_with_best(cropped, template_path, threshold)
    if match is not None:
        return name, val, None  # scale=None for original
    return None


def process_resized(name, cropped, threshold):
    """Try matching with resizing."""
    template_path = os.path.join('names', name)
    match, val, scale = match_template_resized(cropped, template_path, threshold)
    if match is not None:
        return name, val, scale
    return None


# === Main function ===
def get_trader_name(image, threshold=0.9, resized_threshold=0.85, max_workers=8):
    """Detect trader name using config first, then fallback to threaded search."""
    name_templates = fnmatch.filter(os.listdir('names'), '*.png')

    height, width = image.shape[:2]
    square_size = height // 2
    cropped = image[0:square_size, square_size:width]

    # === Step 1: Try preferred template from config ===
    preferred_name = get_config("trader_name")
    preferred_accuracy = get_config("trader_accuracy")
    preferred_method = get_config("trader_method")  # "original" or "resized"
    preferred_scale = get_config("trader_scale")    # only valid if resized

    if preferred_name and preferred_accuracy and preferred_method:
        template_path = os.path.join('names', preferred_name)

        if preferred_method == "original":
            match, val = match_template_with_best(cropped, template_path, threshold)
        else:  # resized method
            match, val, scale = match_template_resized(cropped, template_path, resized_threshold)

        if match is not None and np.isclose(val, float(preferred_accuracy), rtol=1e-3, atol=1e-4):
            Print(f"✅ Config template {preferred_name} matched with {preferred_method}, acc={val:.3f}")
            return preferred_name.split('.')[0]
        else:
            Print(f"⚠ Config template {preferred_name} failed (val={val:.3f}), checking others...")

    # === Step 1: Parallel search (original size) ===
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_original, name, cropped, threshold): name for name in name_templates}
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                res_name, val, scale = result
                Print(f"✔ Template {res_name} found at original size")
                executor.shutdown(cancel_futures=True)

                # Save to config
                update_config("trader_name", res_name)
                update_config("trader_accuracy", val)
                update_config("trader_method", "original")
                update_config("trader_scale", scale)

                return res_name.split('.')[0]

    # === Step 2: Parallel search (resized templates) ===
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_resized, name, cropped, resized_threshold): name for name in name_templates}
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                res_name, val, scale = result
                Print(f"✔ Template {res_name} found after resizing (scale={scale})")
                executor.shutdown(cancel_futures=True)

                # Save to config
                update_config("trader_name", res_name)
                update_config("trader_accuracy", val)
                update_config("trader_method", "resized")
                update_config("trader_scale", scale)

                return res_name.split('.')[0]

    # === Step 3: Nothing found ===
    Print("✖ No trader name matched.")
    return "unknown"