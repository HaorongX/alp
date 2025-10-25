import requests
import json
import re
import unicodedata

def clean_string(text):
    cleaned_text = ''.join(ch for ch in text if unicodedata.category(ch)[0] != 'C') # Remove control characters
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip() # Merge multiple spaces and strip leading/trailing whitespace
    cleaned_text = re.sub(r'\(\s*[a-z]+\s*\)', '', cleaned_text) # Question number
    cleaned_text = re.sub(r'^\d+', '', cleaned_text) # remove leading question numbers
    cleaned_text = cleaned_text.replace('.', '') # Remove any dot
    cleaned_text = re.sub(r'([a-z])([A-Z])', r'\1 \2', cleaned_text)  # add missing spaces
    cleaned_text = re.sub(r'\[\s*\d+\s*\]', '', cleaned_text) # mark worth
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    return cleaned_text.lower()

def ocr(base64_img):
    global config
    payload={
        'language': 'eng',
        'isOverlayRequired': 'false',
        'iscreatesearchablepdf': 'false',
        'issearchablepdfhidetextlayer': 'false',
        'isTable': 'true',
        'OCREngine': '2',
        'base64Image': 'data:image/png;base64,'
    }
    url = config["OCRendPoint"]
    headers = { 'apikey': config["OCRkey"] }
    payload['base64Image'] += base64_img
    response = requests.request("POST", url, headers=headers, data=payload)
    return clean_string(json.loads(response.text, strict = False)["ParsedResults"][0]["ParsedText"])

config = json.load(open("config.json"))
with open("./sample_data.txt", "r") as f:
    sample = f.read()
print(ocr(sample))