import sys
import fitz
from pypdf import PdfReader, PdfWriter
from pdf2image import convert_from_path
import numpy as np

if __name__ == "__main__":
    reader = PdfReader(sys.argv[1])
    output = PdfWriter()

    for i in range(1, len(reader.pages)): # Skip information page
        page = reader.pages[i]
        text = page.extract_text()
        if text.find("GENERIC MARKING PRINCIPLE") == -1 and text.find("Mark scheme abbreviations") == -1 and text.find("Mechanics of Marking") == -1:
            p = reader.pages[i]
            output.add_page(p)
    reader.close()
    
    with open(sys.argv[1].replace('.pdf', '_processed.pdf'), 'wb') as f:
        output.write(f)