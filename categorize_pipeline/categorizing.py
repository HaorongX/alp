import re
import cv2
import requests
import json
import sys
import os
import sqlite3


payload={
    'language': 'eng',
    'isOverlayRequired': 'false',
    'iscreatesearchablepdf': 'false',
    'issearchablepdfhidetextlayer': 'false',
    'isTable': 'true',
    'OCREngine': '2',
    'base64Image': 'data:image/png;base64,'
}

config = json.load(open("config.json"))
url = config["OCRendPoint"]

headers = {
  'apikey': config["OCRkey"]
}

with open("./sample_data.txt", "r") as f:
    sample = f.read()
    payload['base64Image'] += sample

response = requests.request("POST", url, headers=headers, data=payload)
print(json.loads(response.text, strict = False)["ParsedResults"][0]["ParsedText"].strip())