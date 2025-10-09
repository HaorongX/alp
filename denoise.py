from pytesseract import image_to_string
import cv2
import re
from unidecode import unidecode
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from spellchecker import SpellChecker

def clean_ocr_text(text):
    text = unidecode(text)
    
    text = re.sub(r'(?<!\w)[1lI](?=\w)', 'l', text)
    text = re.sub(r'\b0\b', 'o', text)
    text = re.sub(r'[^A-Za-z0-9\s.,;:!?\'"-]', '', text)
    text = text.lower()
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'(.)\1{4,}', '', text)
    text = re.sub(r'(?:^|\s)([cex]+)(?=\s|$)', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'(?:\b\w{1,2}\b\s*){4,}', '', text)
    text = re.sub(r'[^\w\s]{3,}', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    tokens = word_tokenize(text)
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words]
    
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(word) for word in tokens]
    
    return ' '.join(tokens)

def clean_short_nonwords(text):
    words = text.split()
    spell = SpellChecker()
    cleaned = []
    for word in words:
        lw = word.lower()
        if len(lw) > 2:
            cleaned.append(word)
    return ' '.join(cleaned)

def denoise(image):
    text = clean_short_nonwords(clean_ocr_text(image_to_string(image, lang='eng', config='--psm 6')))
    spell = SpellChecker()
    words = text.split()
    misspelled = spell.unknown(words)
    corrected_words = [
        spell.correction(word) if word in misspelled else word
        for word in words
    ]
    return ' '.join(corrected_words)