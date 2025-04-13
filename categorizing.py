import json
import cv2
import numpy as np
from pytesseract import image_to_string
import sys

if __name__ == "__main__":
    keywords = json.load(open("keywords.json", "r"))
    image = cv2.imread(sys.argv[1])
    content = image_to_string(image, lang='eng', config='--psm 6').lower()
    ans = []
    for i in keywords.keys():
        for j in keywords[i]:
            if content.find(j) != -1:
                print(f"Found keyword: {j}")
                ans.append(i)
                break
    print(ans)