import cv2
from pdf2image import convert_from_path
import numpy as np
import sys
import re
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from tesserocr import PyTessBaseAPI, PSM
from PIL import Image

cache_to_binary = {}
tessdata_dir = "/usr/share/tesseract/tessdata"

def to_binary(image, cache_key):
    if cache_to_binary.get(cache_key) is not None:
        return cache_to_binary[cache_key]
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Simple adaptive threshold often works better than complex morphology
    binary_out = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    binary_out = cv2.cvtColor(binary_out, cv2.COLOR_GRAY2BGR)
    
    cache_to_binary[cache_key] = binary_out
    return binary_out

def clear_cache():
    global cache_to_binary
    cache_to_binary = {}

def search_for_next_q(images, start_page, start_y, QUESTION_INDEX_RANGE, mode, offset):
    current_page = start_page
    current_y = start_y + offset

    while current_page < len(images):
        image = np.array(images[current_page])
        MAX_Y = image.shape[0]
        MAX_X = image.shape[1]
        
        cache_key = (current_page, MAX_Y, MAX_X)
        binary_out = to_binary(image, cache_key)

        gray = cv2.cvtColor(binary_out, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)[1]

        # Find all external contours (shapes) in the specified region
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter contours to find potential question numbers
        candidates = []
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            
            # Filter by location (is it in the right column and below the last found item?)
            # and by size (is it plausibly a character and not just noise or a large graphic?)
            if (y >= current_y and
                QUESTION_INDEX_RANGE[0] <= x < QUESTION_INDEX_RANGE[1] and
                5 < h < 50 and 2 < w < 50): # These size constraints may need tuning
                candidates.append((x, y, w, h))

        # Sort candidates from top-to-bottom to process in order
        candidates.sort(key=lambda c: c[1])

        for x, y, w, h in candidates:
            y1_crop = max(y - 15, 0)
            y2_crop = min(y + h + 15, MAX_Y)
            x1_crop = max(x - 15, 0)
            x2_crop = min(x + w + 80, MAX_X)
            
            section = binary_out[y1_crop:y2_crop, x1_crop:x2_crop]
            
            api = PyTessBaseAPI(path=tessdata_dir, lang='eng', psm=PSM.SINGLE_LINE)
            api.SetImage(Image.fromarray(section))
            text = api.GetUTF8Text().strip()
            
            found = False
            if mode == "main":
                if re.search(r"^\d", text): # e.g., "1.", "2 ", etc.
                    found = True
            elif mode == "secondary":
                if re.search(r"^\([A-Za-z]\)", text): # e.g., "(a)", "(b)", etc.
                    found = True
            
            if found:
                return [current_page, y]

        # If no candidates were found on this page, move to the next one
        current_page += 1
        current_y = 0  # Reset search to the top of the next page

    return [len(images) - 1, MAX_Y]

QUESTION_LR_RANGE = {"main" : (100, 130), "secondary" : (200, 260)}
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

def crop_white(image):
    MAX_Y = image.shape[0]
    white_row_mask = np.all(image == 255, axis=2)
    fully_white_rows = np.all(white_row_mask, axis=1)
    
    to_be_removed = []
    in_white_region = True
    first_blank_line = 0
    
    for i in range(MAX_Y):
        if not fully_white_rows[i] and in_white_region:
            in_white_region = False
            if i - first_blank_line > 200:
                to_be_removed.append((min(first_blank_line + 10, MAX_Y - 1), max(i - 10, 0)))
        elif fully_white_rows[i] and not in_white_region:
            in_white_region = True
            first_blank_line = i
    
    if in_white_region and MAX_Y > 0 and fully_white_rows[MAX_Y - 1]:
        to_be_removed.append((first_blank_line, max(MAX_Y - 10, 0)))
    
    if to_be_removed:
        rows_to_remove = np.concatenate([np.arange(start, end + 1) for start, end in to_be_removed])
        return np.delete(image, rows_to_remove, axis=0)
    
    return image

def process_page_for_cropping(raw_pil_image):
    image_array = np.array(raw_pil_image).copy()
    processed_image = crop_white(image_array)
    return processed_image

def preprocessing(pdf_path):
    print("Pre - processing...")
    raw_images = convert_from_path(pdf_path, 300)
    
    images = []

    with ThreadPoolExecutor(max_workers = 22) as executor:
        futures = []
        
        for i, raw_img in enumerate(raw_images):
            future = executor.submit(process_page_for_cropping, raw_img)
            futures.append(future)
        
        for future in futures:
            images.append(future.result())
            
    del raw_images
    
    return images

def process_sub_questions(i, main_q, qp_name):
    l = [main_q]  # Wrap into list to keep consistent input type
    sub = split_question(l, "secondary")

    result_info = []
    cnt = 0
    res = search_for_next_q(l, 0, 0, QUESTION_LR_RANGE["secondary"], "secondary", QUESTION_OFFSET["secondary"])
    
    primary_statement = None
    if res[1] > 10:  # There is something before the first sub-question
        primary_statement = crop(l, 0, 0, res[0], res[1])

    for j in sub:
        cnt += 1
        # Ensure primary_statement is not None before concatenating to satisfy type-checkers
        if res[1] > 10 and len(sub) != 1 and primary_statement is not None:
            vis = np.concatenate([primary_statement, j], axis=0)
        else:
            vis = j
        out_path = f"./{qp_name}/{i + 1}_{cnt}.png"
        cv2.imwrite(out_path, vis)
    
    result_info.append((i + 1, len(sub)))
    return result_info

def extractqp(qp_name, pdf_path):
    qp_name = "test"
    if not os.path.exists(qp_name):
        os.makedirs(qp_name)

    processed = preprocessing(sys.argv[1])
    main_questions = split_question(processed, "main")
    print(f"{len(main_questions)} questions found in total")

    print("Extracting other questions...")
    with ThreadPoolExecutor(max_workers = 22) as executor:
        futures = [
            executor.submit(process_sub_questions, i, main_questions[i], qp_name)
            for i in range(len(main_questions))
        ]
        
        for f in as_completed(futures):
            results = f.result()
            for q_num, sub_count in results:
                print(f"{sub_count} questions found in question {q_num}")

if __name__ == "__main__":
    extractqp(sys.argv[1], sys.argv[1])