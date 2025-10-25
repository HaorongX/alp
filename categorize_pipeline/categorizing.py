import requests
import json
import re
import unicodedata
from nltk.corpus import stopwords
import nltk
from sklearn.preprocessing import LabelEncoder

def clean_string(text):
    cleaned_text = ''.join(ch for ch in text if unicodedata.category(ch)[0] != 'C') # Remove control characters
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip() # Merge multiple spaces and strip leading/trailing whitespace
    cleaned_text = re.sub(r'\(\s*[a-z]+\s*\)', '', cleaned_text) # Question number
    cleaned_text = re.sub(r'^\d+', '', cleaned_text) # remove leading question numbers
    cleaned_text = cleaned_text.replace('.', '') # Remove any dot
    cleaned_text = re.sub(r'([a-z])([A-Z])', r'\1 \2', cleaned_text)  # add missing spaces
    cleaned_text = re.sub(r'\[\s*\d+\s*\]', '', cleaned_text) # mark worth
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    cleaned_text = re.sub(r' - ', ' ', cleaned_text) # isolate dash
    cleaned_text = cleaned_text.lower()
    try:
        stop_words = stopwords.words('english')
        cleaned_text = ' '.join(word for word in cleaned_text.split(' ') if word not in stop_words)
    except LookupError:
        nltk.download('stopwords')
        stop_words = stopwords.words('english')
        cleaned_text = ' '.join(word for word in cleaned_text.split(' ') if word not in stop_words)
    return cleaned_text

def stemm_text(text):
    global stemm_text
    text = ' '.join(stemmer.stem(word) for word in text.split(' '))
    return text

def ocr(base64_img):
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

def __init__():
    global config
    global stemmer
    stemmer = nltk.SnowballStemmer("english")
    config = json.load(open("config.json"))

__init__()
with open("./sample_data.txt", "r") as f:
    sample = f.read()
print(stemm_text(ocr(sample)))