import cv2 
import os
# from main import Print
from std_out import Print,play_error_sound,log_exception
import numpy as np
import threading



def match_template_or_none(image, template_path):
    if not os.path.exists(template_path):
        return None
    template = cv2.imread(template_path)
    if template is None:
        return None
    result_match = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result_match)
    # Print(f"Pair: {template_path} , Val : {max_val}")
    return max_val 


def match_at_scale(image, original_template, scale, mode, threshold, all_points_lock, all_points):
    template = cv2.resize(original_template, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
    h, w = template.shape[:2]

    if h > image.shape[0] or w > image.shape[1]:
        return

    result = cv2.matchTemplate(image, template, mode)
    is_low_better = mode in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]

    if is_low_better:
        locations = np.where(result <= threshold)
    else:
        locations = np.where(result >= threshold)
    # print(locations)
    scale_points = [(pt[0], pt[1], w, h, result[pt[1], pt[0]]) for pt in zip(*locations[::-1])]
    # print(scale_points)
    # print("\n")

    # Use lock to safely append to shared list
    with all_points_lock:
        all_points.extend(scale_points)


def match_template(image, template_path, threshold=0.75, mode=cv2.TM_CCOEFF_NORMED ,check_x_scale = False):
    
    if not os.path.exists(template_path):
        return image, []

    original_template = cv2.imread(template_path)
    if original_template is None:
        return image, []

    matches = []
    all_points = []
    all_points_lock = threading.Lock()

    threads = []
    for scale in np.linspace(0.5, 2.5, 40):
        t = threading.Thread(target=match_at_scale, args=(image, original_template, scale, mode, threshold, all_points_lock, all_points))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
    # print(all_points)
    if all_points:
        max_value = max(item[-1] for item in all_points)
    else:
        max_value = 0
    return max_value




def get_chart_num(image):
    
    height,width = image.shape[:2]
    cropped_image = image[0:height//5,width - width//3 : width]
    # cv2.imshow("cropeped",cropped_image)
    # cv2.waitKey(0)
    single_val = match_template(cropped_image,"templates/single_chart.png")
    print("single",single_val)
    double_val = match_template(cropped_image,"templates/double_chart.png")
    print("double",double_val)
    # triple_val = match_template(image,"templates/triple_chart.png")
    # print("triple",triple_val)
    quadruple_val = match_template(cropped_image,"templates/quadruple_chart.png")
    print("quadruple",quadruple_val)
    
    chart_num = [single_val,double_val,0,quadruple_val]
    max_val = max(chart_num)
    max_val_index = chart_num.index(max_val)
    return max_val_index+1
    
    

    
if __name__ == "__main__":
    image = cv2.imread("screen.png")
    c=get_chart_num(image)
    print(c)
    # get_chart_num(image)