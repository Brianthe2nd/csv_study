import cv2
import numpy as np
import os

def measure_blurriness(image):
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Compute Laplacian
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return laplacian_var

img_paths = ["nas.png"]
pairs = os.listdir("pairs_2_resized")
# img_paths.extend(pairs)
for pair in pairs:
    img_paths.append(f"pairs_2_resized/{pair}")
img_paths.append("templates/pair_search.png")
# Example usage
mini = 9999999999999
for img_path in img_paths:
    img = cv2.imread(img_path)
    score = measure_blurriness(img)
    if score < mini:
        mini = score
    # print(f"Blurriness score for {img_path}: {score}")
    if score < 100:  # You can tune this threshold
        print("Image is likely blurry")
    else:
        print("Image is sharp")

print(mini)

# def blur_to_level(image, target_blur, step=3):
#     blurred = image.copy()
#     current_blur = measure_blurriness(blurred)

#     while current_blur > target_blur:
#         # Increase blur using GaussianBlur
#         blurred = cv2.GaussianBlur(blurred, (step, step), 0)
#         current_blur = measure_blurriness(blurred)

#     return blurred

# cv2.imwrite("blurred_pair_search.png",blur_to_level(cv2.imread("templates/pair_search.png"),mini))
# pairs = os.listdir("pairs_2")
# for pair in pairs:
#     cv2.imwrite(f"blurred_pairs_2/{pair}",blur_to_level(cv2.imread(f"pairs_2/{pair}"),mini))

