from pdf2image import convert_from_path
from alive_progress import alive_bar
import numpy as np
import cv2
from pytesseract import image_to_data, Output
import re
from toolbox import crop, crop_white_margin
import sys
import os

def preprocessing(pdf_path):
    raw_images = convert_from_path(pdf_path, 300) # Specify image quality
    images = []
    print("Pre - processing...")
    with alive_bar(len(raw_images)) as bar:
        for i in raw_images:
            images.append((np.array(i).copy()))
            bar()
    del raw_images
    return images

def get(image):
    data = image_to_data(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), output_type = Output.DICT, lang='eng', config='--psm 6')
    question_coords = []
    question_regex = r"^\d{1,2}(\([a-z]\))?(\((i{1,3}|iv|v|vi|vii|viii|ix|x|xi)\))?$"
    MAX_X = image.shape[1]
    min_left = MAX_X
    for i in range(len(data['text'])):
        word = data['text'][i].strip()
        if re.match(question_regex, word):
            top, left = data['top'][i], data['left'][i]
            if left < min_left:
                min_left = left
            question_coords.append((top, left, word))
    results = []
    print(data)
    for i in question_coords:
        if not (i[1] > (min_left + 50)):
            results.append(i)
        else:
            print("abandon", i[2], i[1], min_left + 50, i[1] > (min_left + 50))
    del question_coords
    print(results)
    return results

def process(image, data):
    MAX_Y = image.shape[0]
    ms = []
    for i in data:
        top, left, word = i[0], i[1], i[2]
        images = [image]
        bottom = top + 50
        while image[bottom, left][0] == 255 and image[bottom, left][1] == 255 and image[bottom, left][2] == 255 and bottom < MAX_Y:
            bottom += 1
        if str(word).find('(') == -1:
            word = str(word) + '(a)'
        ms.append((word, crop(images, 0, max(0, top - 10), 0, min(MAX_Y - 1, bottom))))
    return ms 

if __name__ == "__main__":
    images = preprocessing(sys.argv[1])
    ms_name = re.search(r"9618_[sw]\d{2}_ms_\d{2}", sys.argv[1]).group(0)
    if not os.path.exists(ms_name):
        os.makedirs(ms_name)
    ms_raw = []
    print("Splitting...")
    with alive_bar(len(images)) as bar:
        for i in range(len(images)):
            ms_raw += process(images[i], get(images[i]))
            bar()
    ms = []    
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