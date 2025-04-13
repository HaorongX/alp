from pdf2image import convert_from_path
from alive_progress import alive_bar
import numpy as np
import cv2
from pytesseract import image_to_string
import re
from toolbox import crop_white_margin
import sys
import os
import random

def preprocessing(pdf_path):
    raw_images = convert_from_path(pdf_path, 300) # Specify image quality, must not be changed
    images = []
    print("Pre - processing...")
    with alive_bar(len(raw_images)) as bar:
        for i in raw_images:
            images.append((np.array(i).copy()))
            bar()
    del raw_images
    return images

def get_left_margin(image):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    global THE_COLUMN
    global L_MARGIN
    THE_STARTING_Y = 270
    for i in range(0, image.shape[1]):
        if image[THE_STARTING_Y + 20][i] != 255:
            L_MARGIN = i
            break
    THE_COLUMN = L_MARGIN + 7

def next_black_bondary(image, y):
    for i in range(y, image.shape[0]):
        if not image[i][THE_COLUMN] == 255:
            return i
    return -1

def get(image):
    THE_STARTING_Y = 270
    OFFSET = 55
    PROBLEM_WIDTH = 260
    MAX_Y = image.shape[0]
    MAX_X = image.shape[1]
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(image, 170, 255, cv2.THRESH_BINARY)
    image = thresh
    first = next_black_bondary(image, THE_STARTING_Y)
    second = next_black_bondary(image, first + 3)
    sections = []
    while second != -1:
        section = image[min(first + 3, MAX_Y) : min(first + 90, MAX_Y), L_MARGIN + 3 : L_MARGIN + PROBLEM_WIDTH]
        text = image_to_string(section, config='--psm 7 -c tessedit_char_blacklist=A').strip() # The image contains of a single line of text
        if re.search(r"^\d{1,2}(\([a-z]\))?(\((i{1,3}|iv|v|vi|vii|viii|ix|x|xi)\))?$", text) != None:
            if len(text) <= 2:
                text += "(a)"
            sections.append((text, image[first : second, 0 : MAX_X]))
        first = second
        second = next_black_bondary(image, first + OFFSET)
    return sections

if __name__ == "__main__":
    images = preprocessing(sys.argv[1])
    ms_name = re.search(r"9618_[sw]\d{2}_ms_\d{2}", sys.argv[1]).group(0)
    if not os.path.exists(ms_name):
        os.makedirs(ms_name)
    get_left_margin(images[0])
    ms_raw = []
    print("Splitting...")
    with alive_bar(len(images)) as bar:
        for i in images:
            ms_raw += get(i)
            bar()

    i = 0
    while i < len(ms_raw):
        index = re.search(r"^\d{1,2}(\([a-z]\))", ms_raw[i][0]).group()
        image = ms_raw[i][1]
        j = i + 1
        while j < len(ms_raw) and re.search(r"^\d{1,2}(\([a-z]\))", ms_raw[j][0]).group() == index:
            image = np.concatenate((image, ms_raw[j][1]), axis=0)
            j += 1
        i = j
        image = crop_white_margin(image)
        cv2.imwrite(f"./{ms_name}/" + index[:-3] + '_' + str(ord(index[-2]) - ord('a') + 1) + ".png", image)