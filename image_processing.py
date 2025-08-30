import cv2
import numpy as np
import os
from std_out import Print,play_error_sound,log_exception
from logo import check_logo

def get_top_left(image):
    scales = np.linspace(0.2, 2, 50)
    logo_exists, total_matches,matches = check_logo(image,scales,True,"templates/logo.png")
    print("logo_exists:",logo_exists)
    if logo_exists:
        match_ = matches[0]
        top_left = match_[0]
    else:
        top_left = None
    
    return top_left,logo_exists,total_matches,matches

def get_top_right(or_image):
    scales = np.linspace(0.5, 2, 100)
    height, width = or_image.shape[:2]
    x_add = (3*(width // 5))
    y_add = height // 2
    image = or_image[0:y_add, x_add:width]

    logo_exists, total_matches,matches = check_logo(image,scales,True,"templates/top_right.png",custom_image=True)
    if logo_exists:
        match_ = matches[0]
        top_right = match_[0]
        width = match_[1][1]
        x,y = top_right
        cv2.rectangle(image, (x,y), (x+  20,y +10), (0, 255, 0), 2)
        # cv2.imshow("top_right",image)
        # cv2.waitKey(0)        
        top_right = (x+(width*2)+x_add,y)
        

    else:
        top_right = None
    
    return top_right

def get_bottom_right(or_image):
    scales = np.linspace(0.5, 2, 100)
    height, width = or_image.shape[:2]
    y_add = height // 2
    x_add = (3*(width // 5))
    image = or_image[ y_add: height, x_add:width]

    logo_exists, total_matches,matches = check_logo(image,scales,True,"templates/bottom_right.png",custom_image=True)
    if logo_exists:
        match_ = matches[0]
        bottom_right = match_[0]
        width = match_[1][1]
        x,y = bottom_right
        bottom_right = (x+(width*2)+x_add,y+y_add)
        
        # cv2.rectangle(image, (x,y), (x+ + 20,y +10), (0, 255, 0), 2)
        # cv2.imshow("bottom_right",image)
        # cv2.waitKey(0)
    else:
        bottom_right = None
    
    return bottom_right

def get_bottom_left(image):
    bottom_left_template_path="templates/bl.png"
    # height, width = image.shape[:2]
    # image = image[height // 2 : height, 0:width//3]
    # cv2.imshow("bottom_left",image)
    # cv2.waitKey(0)
    def match_template_or_none(image, template_path):
        if not os.path.exists(template_path):
            # Print(f"Template not found: {template_path}")
            return None
        template = cv2.imread(template_path)
        if template is None:
            # Print(f"Failed to read template: {template_path}")
            return None
        result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        threshold = 0.7  # adjust as needed
        return max_loc if max_val > threshold else None
    
    loc = match_template_or_none(image, bottom_left_template_path)
    return loc
    

def crop_chart_region(image):
    img_height, img_width = image.shape[:2]
    
    top_left,logo_exists,total_matches,matches = get_top_left(image)
    top_right = None
    bottom_left = get_bottom_left(image)
    bottom_right = None
    default_top = 0
    default_left = 0
    default_bottom = img_height
     
    if top_left is None:
        if bottom_left is not None:
            x1 = bottom_left[0]
            y1 = default_top
        else:
            x1 = default_left
            y1 = default_top
    
    else:
        x1, y1 = top_left
        
    if top_right is None:
        if bottom_right is not None:
            x2 = bottom_right[0]
        else:
            x2 = img_width
    else:
        x2 = top_right[0]
        
    if bottom_left is None:
        if bottom_right is not None:
            y2 = bottom_right[1]
        else:
            y2 = img_height
    else:
        y2 = bottom_left[1]
            

    # Ensure values are within image boundaries
    # x1 = max(0, min(x1, img_width))
    # x2 = max(0, min(x2, img_width))
    # y1 = max(0, min(y1, img_height))
    # y2 = max(0, min(y2, img_height))

    # if y2 <= y1 or x2 <= x1:
    #     cropped = image.copy()
    # else:
    cropped = image[y1:y2, x1:x2]


    return cropped,logo_exists,total_matches,matches




def reduce_close_points_exact(points, threshold=3):
    reduced = []
    used = [False] * len(points)

    for i, (x1, y1) in enumerate(points):
        if used[i]:
            continue
        reduced.append((x1, y1))
        used[i] = True

        for j in range(i + 1, len(points)):
            x2, y2 = points[j]
            if abs(x1 - x2) < threshold or abs(y1 - y2) < threshold:
                used[j] = True

    return reduced


def find_trade_buttons(trade_templates,chart_img, threshold=0.95):
    # Load the template
    available_trades={}
    for template in trade_templates:
      # if "sell_gray" in template or "buy_gray" in template:
      #   threshold = 0.8
      trade_template_path = f"trade_templates/{template}"
      trade_template = cv2.imread(trade_template_path)
      if trade_template is None:
          raise FileNotFoundError(f"Template not found at {trade_template_path}")

      trade_h, trade_w = trade_template.shape[:2]

      # Perform template matching
      result = cv2.matchTemplate(chart_img, trade_template, cv2.TM_CCOEFF_NORMED)

      # Find all locations where match is above threshold
      y_coords, x_coords = np.where(result >= threshold)
      matches = list(zip(x_coords, y_coords))  # (x, y) format for OpenCV

      # Draw rectangles on the matches
    #   for (x, y) in matches:
    #       cs=cv2.rectangle(chart_img, (x, y), (x + trade_w, y + trade_h), (1,1,1), 1)
    #       cv2_imshow(cs)
      matches=reduce_close_points_exact(matches)

      # Print(f"The number of matches for {template.split('.')[0]} is {len(matches)}")
      # Print(matches)
      # if len(matches) != 0:
      #   available_trades.append(template.split(".")[0])
      available_trades[template.split(".")[0]] = len(matches)


      # previous_boxes = []

      # for trade_b in matches:
      #     previous_box_x = trade_b[0] - width  # shift left
      #     previous_boxes.append((previous_box_x, trade_b[1]))  # store as tuple for clarity

      # for (x, y) in previous_boxes:
      #     cs=cv2.rectangle(chart_img, (x, y), (x + trade_w, y + trade_h), (1,1,1), 1)
      #     cv2_imshow(cs)

      # Print("The coordinates of the previous boxes are:")
      # Print(previous_boxes)

    return available_trades


# for idx, (x, y) in enumerate(trade_buttons):
#     Print(f"Trade #{idx + 1} found at: ({x}, {y})")


if __name__ == "__main__":
    # image = cv2.imread("screen.png")
    # from screen import capture_screen
    # image = capture_screen(2)
    # chart = crop_chart_region(image = image)
    # cv2.imshow("chart",chart)
    # cv2.waitKey(0)
    # cv2.imwrite("chart.png",chart)
    image = cv2.imread("chart.png")
    top_left,logo_exists,total_matches,matches = get_top_left(image)
    print("logo exists: ",logo_exists)
    