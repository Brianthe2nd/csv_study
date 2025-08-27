import cv2
import numpy as np
from matplotlib import pyplot as plt
from chart_num import get_chart_num

def detect_chart_layout(image):
    height, width = image.shape[:2]

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150, apertureSize=3)

    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=200, maxLineGap=15)

    vertical_lines = []
    horizontal_lines = []

    x_min, x_max = int(0.2 * width), int(0.8 * width)
    y_min, y_max = int(0.2 * height), int(0.8 * height)

    min_vertical_len = int(0.5 * height)
    min_horizontal_len = int(0.5 * width)

    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if abs(x1 - x2) < 10:
                line_len = abs(y2 - y1)
                if x_min <= x1 <= x_max and line_len >= min_vertical_len:
                    vertical_lines.append((x1, y1, x2, y2))
            elif abs(y1 - y2) < 10:
                line_len = abs(x2 - x1)
                if y_min <= y1 <= y_max and line_len >= min_horizontal_len:
                    horizontal_lines.append((x1, y1, x2, y2))

    x_dividers = sorted(set([x1 for x1, _, _, _ in vertical_lines]))
    y_dividers = sorted(set([y1 for _, y1, _, _ in horizontal_lines]))
    # layout = 4 if len(x_dividers) >= 1 and len(y_dividers) >= 1 else 1
    chart_nums = get_chart_num(image)
    if len(x_dividers) == 0 and len(y_dividers) == 0:
        layout = 1
    elif len(x_dividers) == 1 and len(y_dividers) == 0:
        if chart_nums == 2:
            layout = 2
        else:
            layout = 1   
    elif len(x_dividers) == 2 and len(y_dividers) == 0:
        if chart_nums == 3:
            layout = 3
        else:
            layout = 1
    elif len(x_dividers) == 1 and len(y_dividers) == 1:
        if chart_nums == 4:
            layout = 4
        else:
            layout = 1
    else:
      layout =1


    return layout, x_dividers, y_dividers
if __name__ == "__main__":
    image = cv2.imread('screen.png')
    num,x,y=detect_chart_layout(image)
    print(num,x,y)
