from pdf2image import convert_from_path
import numpy as np
import cv2
from pytesseract import image_to_string
import re
import sys
import os
from multiprocessing import Pool, cpu_count
from pypdf import PdfReader, PdfWriter

def crop_white_margin(image):
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

def preprocessing(pdf_path):
    raw_images = convert_from_path(pdf_path, 300) # Specify image quality, must not be changed
    images = []
    for i in raw_images:
        images.append((np.array(i)))
    del raw_images
    return images

def get_left_margin(image):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    THE_STARTING_Y = 300
    for i in range(0, image.shape[1]):
        if image[THE_STARTING_Y + 20][i] != 255:
            L_MARGIN = i
            break
    THE_COLUMN = L_MARGIN + 7
    return (L_MARGIN, THE_COLUMN)

def next_black_bondary(image, y, THE_COLUMN):
    column = image[y:, THE_COLUMN]
    black_pixels = np.where(column != 255)[0]
    
    if len(black_pixels) > 0:
        return y + black_pixels[0]
    return -1

def get(image):
    L_MARGIN, THE_COLUMN = get_left_margin(image)
    original = image
    THE_STARTING_Y = 270
    OFFSET = 55
    PROBLEM_WIDTH = 230
    MAX_Y = image.shape[0]
    MAX_X = image.shape[1]
    allowed_chars = '0123456789abcdefghijklmnopqrstuvwxyz()'
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image = cv2.bilateralFilter(image, 9, 75, 75)
    _, image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    first = next_black_bondary(image, THE_STARTING_Y, THE_COLUMN)
    second = next_black_bondary(image, first + 3, THE_COLUMN)
    sections = []
    while second != -1:
        section = image[min(first + 3, MAX_Y) : min(first + 90, MAX_Y), L_MARGIN + 5 : L_MARGIN + PROBLEM_WIDTH]
        if cv2.countNonZero(255 - section) < 200:
            first = second
            second = next_black_bondary(image, first + OFFSET, THE_COLUMN)
            continue
        text = image_to_string(section, config='--psm 6 -c load_system_dawg=0 -c load_freq_dawg=0 -c tessedit_char_whitelist=' + allowed_chars).strip().lower() # The image contains of a single line of text
        if re.search(r"^\d{1,2}(\([a-z]\))?(\((i{1,3}|iv|v|vi|vii|viii|ix|x|xi)\))?$", text) != None:
            if len(text) <= 2:
                text += "(a)"
            sections.append((text, original[first : second, 0 : MAX_X]))
        first = second
        second = next_black_bondary(image, first + OFFSET, THE_COLUMN)
    return sections


def process_single_page(args):
    """Process one page and return with its page number"""
    image, page_num = args
    sections = get(image)
    # Tag each section with page number for sorting later
    return [(text, img, page_num) for text, img in sections]

if __name__ == "__main__":
    reader = PdfReader(sys.argv[1])
    output = PdfWriter()

    for i in range(1, len(reader.pages)): # Skip information page
        page = reader.pages[i]
        text = page.extract_text()
        if text.find("General Marking Guidance") ==-1 and text.find("Pearson") == -1 and text.find("GENERIC MARKING PRINCIPLE") == -1 and text.find("Mark scheme abbreviations") == -1 and text.find("Mechanics of Marking") == -1:
            p = reader.pages[i]
            output.add_page(p)
    reader.close()
    
    with open("test.pdf", 'wb') as f:
        output.write(f)
    os.remove(sys.argv[1])
    images = preprocessing("test.pdf")
    ms_name = "test"
    if not os.path.exists(ms_name):
        os.makedirs(ms_name)
    
    get_left_margin(images[0])
    
    num_processes = max(1, cpu_count() - 1)
    
    if len(images) > 1 and num_processes > 1:
        # Prepare arguments with page numbers
        args_list = [(img, idx) for idx, img in enumerate(images)]
        
        with Pool(processes=num_processes) as pool:
            results = pool.map(process_single_page, args_list)
        
        # Flatten and sort by page number to maintain order
        ms_raw_with_page = []
        for page_sections in results:
            ms_raw_with_page.extend(page_sections)
        
        # Sort by page number to ensure correct order
        ms_raw_with_page.sort(key=lambda x: x[2])
        
        # Remove page numbers for merging
        ms_raw = [(text, img) for text, img, page_num in ms_raw_with_page]
    else:
        ms_raw = []
        for img in images:
            ms_raw += get(img)
    
    # Original merging logic (unchanged)
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
        cv2.imwrite(f"./{ms_name}/{index[:-3]}_{ord(index[-2]) - ord('a') + 1}.png", image)