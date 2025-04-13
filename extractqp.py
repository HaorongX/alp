import cv2
from pdf2image import convert_from_path
import numpy as np
from pytesseract import image_to_string
import sys
import re
import os
from alive_progress import alive_bar
from toolbox import crop, to_binary, clear_cache

def search_for_next_q(images, start_page, start_y, QUESTION_INDEX_RANGE, mode, offset): # Search for the next question in bold, skip the current one indicated by start_page and start_y

    current_page = start_page
    current_y = start_y + offset # Skip the current one so move 100 pixels downwards
    while current_page < len(images):
        image = np.array(images[current_page])
        MAX_Y = np.array(image).shape[0]
        binary_out = to_binary(image)
        inverted = 255 - binary_out

        y1 = current_y
        flag = False
        j = y1
        while j < MAX_Y:
            if inverted[j].sum() == 0: 
                j += 1
                continue
            for i in range(QUESTION_INDEX_RANGE[0], QUESTION_INDEX_RANGE[1]):
                if binary_out[j, i][0] == 0 and binary_out[j, i][1] == 0 and binary_out[j, i][2] == 0: ## RGB = (0, 0, 0) Black AND is a question index
                    section = binary_out[max(j - 20, 0) : min(j + 80, MAX_Y), i - 30 : i + 100]

                    if mode == "main":
                        if re.search(r"^\d", image_to_string(section, lang='eng', config='--psm 6')) != None:
                            y1 = j
                            flag = True
                            break
                        else:
                            j += 50 # Skip the next 50 pixels
                            break
                    elif mode == "secondary":
                        if re.search(r"^\([A-Za-z]\)", image_to_string(section, lang='eng', config='--psm 6')) != None:
                            y1 = max(j - 20, 0)
                            flag = True
                            break
                        else:
                            j += 50 # Skip the next 50 pixels
                            break
            if flag:
                break
            j += 1
        if flag:
            return [current_page, y1]
        
        current_page += 1 # No question found, move to the next page
        current_y = 0
    
    # Finally, if no question is found, return the last page
    return [current_page - 1, MAX_Y]

QUESTION_LR_RANGE = {"main" : (200, 270), "secondary" : (290, 360)}
QUESTION_OFFSET = {"main" : 20, "secondary" : 0}

def split_question(images, type, starting_page = 0): # Process main questions numbered 1, 2, 3, etc.
    MAX_Y = np.array(images[len(images) - 1]).shape[0]

    LR_RANGE = QUESTION_LR_RANGE[type]
    FIRST_OFFSET = QUESTION_OFFSET[type]
    OFFSET = 100
    first = search_for_next_q(images, starting_page, 0, LR_RANGE, type, FIRST_OFFSET)
    if first == [len(images) - 1, MAX_Y]: # No question found:
        return [crop(images, first[0], 0, len(images) - 1, MAX_Y)] # Return the last page
    second = search_for_next_q(images, first[0], first[1], LR_RANGE, type, OFFSET) # Search for the second question
    cropped = []
    while second != [len(images) - 1, MAX_Y]:
        cropped.append(crop(images, first[0], first[1], second[0], second[1])) # Crop the image between the two questions
        first = second
        second = search_for_next_q(images, first[0], first[1], LR_RANGE, type, OFFSET)

    cropped.append(crop(images, first[0], first[1], second[0], second[1])) # Last question
    clear_cache()
    return cropped

def crop_white(image):
    MAX_Y = np.array(image).shape[0]
    white_row_mask = np.all(image == 255, axis=2)
    fully_white_rows = np.all(white_row_mask, axis=1)
    flag = True
    first_blank_line = 0
    to_be_removed = []
    for i in range(0, MAX_Y):
        if (not fully_white_rows[i]) and flag:
            flag = False
            if i - first_blank_line > 200:
                to_be_removed.append((min(first_blank_line + 10, MAX_Y - 1), max(i - 10, 0)))
        elif fully_white_rows[i] and flag == False:
            flag = True
            first_blank_line = i
    if flag == True and fully_white_rows[MAX_Y - 1]:
        to_be_removed.append((first_blank_line, max(MAX_Y - 10, 0)))
    if len(to_be_removed) > 0:
        rows_to_remove = np.concatenate([np.arange(start, end+1) for start, end in to_be_removed])
        return np.delete(image, rows_to_remove, axis=0)
    return image

def preprocessing(pdf_path):
    raw_images = convert_from_path(pdf_path, 300) # Specify image quality
    images = []
    print("Pre - processing...")
    with alive_bar(len(raw_images)) as bar:
        for i in raw_images:
            images.append(crop_white(np.array(i).copy()))
            bar()
    del raw_images
    return images

if __name__ == "__main__":
    qp_name = re.search(r"9618_[sw]\d{2}_qp_\d{2}", sys.argv[1]).group(0)
    print("Now processing", qp_name)
    if not os.path.exists(qp_name):
        os.makedirs(qp_name)
    processed = preprocessing(sys.argv[1])

    main_questions = split_question(processed, "main")
    print(f"{len(main_questions)} questions found in total\n")

    print("Extracting other questions...")
    with alive_bar(len(main_questions)) as bar:
        for i in range(0, len(main_questions)):
            l = list()
            l.append(main_questions[i])
            sub = split_question(l, "secondary")
            print(f"{len(sub)} questions found in question {i + 1}")
            cnt = 0
            res = search_for_next_q(l, 0, 0, QUESTION_LR_RANGE["secondary"], "secondary", QUESTION_OFFSET["secondary"])
            if  res[1] > 10: # There is something before the first one item
                primary_statement = crop(l, 0, 0, res[0], res[1])
            for j in sub:
                cnt += 1
                if res[1] > 10 and len(sub) != 1:
                    vis = np.concatenate((primary_statement, j), axis=0)
                else:
                    vis = j
                cv2.imwrite(f"./{qp_name}/{i + 1}_{cnt}.png", vis)
            bar()