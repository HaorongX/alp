import numpy as np
import cv2

def crop(image, page1, y1, page2, y2): # Crop the pdf, starting from page1 y1 all the way to page2 y2
    MAX_Y = np.array(image[page1]).shape[0]
    MAX_X = np.array(image[page1]).shape[1]
    if page1 == page2:
        return image[page1][y1 : y2, 0 : MAX_X].copy()
    images_sequence = []
    
    images_sequence.append(image[page1][y1 : MAX_Y, 0 : MAX_X].copy())
    for i in range(page1 + 1, page2):
        images_sequence.append(image[i].copy())
    
    if y2 > 400: # Ignore the last page if it is the blank space at the beginning of a page
        images_sequence.append(image[page2][0 : y2, 0 : MAX_X].copy())

    final_image = images_sequence[0]
    for i in range(1, len(images_sequence)):
        final_image = np.concatenate((final_image, images_sequence[i]), axis=0)
    return final_image

cache_to_binary = {}
def pHash(cv_image):
    h = cv2.img_hash.pHash(cv_image) # 8-byte hash
    pH = int.from_bytes(h.tobytes(), byteorder='big', signed=False)
    return pH

def to_binary(image):
    hash_val = pHash(image)
    if cache_to_binary.get(hash_val) is not None:
        return cache_to_binary[hash_val]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY)[1]
    kernel = np.ones((6,6),np.uint8)
    kernel2 = np.ones((4,4),np.uint8)
    marker = cv2.dilate(thresh,kernel,iterations = 1)
    mask = cv2.erode(thresh,kernel,iterations = 1)
    while True:
        tmp = marker.copy()
        marker = cv2.erode(marker, kernel2)
        marker = cv2.max(mask, marker)
        difference = cv2.subtract(tmp, marker)
        if cv2.countNonZero(difference) == 0:
            break
    marker_color = cv2.cvtColor(marker, cv2.COLOR_GRAY2BGR)
    out = cv2.bitwise_or(image, marker_color)
    binary_out = cv2.threshold(out, 160, 255, cv2.THRESH_BINARY)[1]
    cache_to_binary[hash_val] = binary_out
    return binary_out

def clear_cache():
    global cache_to_binary
    cache_to_binary = {}

def crop_white_margin(image): # This function removes white margins on the left and right side
    left = 0
    right = image.shape[1] - 1
    for i in range(image.shape[1]):
            if not (image[0, i].all() == 255):
                left = i
                break
    for i in reversed(range(image.shape[1])):
            if not (image[0, i].all() == 255):
                right = i
                break
    return image[0: image.shape[0], left : right + 1]