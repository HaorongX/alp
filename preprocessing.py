import sys
import fitz
from pypdf import PdfReader, PdfWriter
from pdf2image import convert_from_path
import numpy as np

def cover_pdf_area_withmargin(input_pdf, output_pdf):
    bar_code = [30, 20, 250, 70]
    block1 = [542, 38, 560, 55]
    block2 = [490, 798, 562, 823]
    block3 = [34, 799, 105, 822]
    qr_code = [170, 805, 187, 824]
    info = [269, 808, 326, 818]
    margin1 = [574, 0, 596, 842]
    margin2 = [0, 0, 21, 847]
    copy_right = [30, 700, 564, 827]
    page_index = [284, 34, 324, 60]
    pdf_document = fitz.open(input_pdf)
    for i in range(0, pdf_document.page_count):
        page = pdf_document.load_page(i)
        page.draw_rect(bar_code, color=(1, 1, 1), fill = (1, 1, 1))
        page.draw_rect(block1, color=(1, 1, 1), fill = (1, 1, 1))
        page.draw_rect(block2, color=(1, 1, 1), fill = (1, 1, 1))
        page.draw_rect(block3, color=(1, 1, 1), fill = (1, 1, 1))
        page.draw_rect(qr_code, color=(1, 1, 1), fill = (1, 1, 1))
        page.draw_rect(info, color=(1, 1, 1), fill = (1, 1, 1))
        page.draw_rect(margin1, color=(1, 1, 1), fill = (1, 1, 1))
        page.draw_rect(margin2, color=(1, 1, 1), fill = (1, 1, 1))
        page.draw_rect(page_index, color=(1, 1, 1), fill = (1, 1, 1))
        if i == pdf_document.page_count - 1:
            page.draw_rect(copy_right, color=(1, 1, 1), fill = (1, 1, 1))
    pdf_document.save(output_pdf)

def cover_pdf_area_withoutmargin(input_pdf, output_pdf):
    info = [18, 794, 590, 825]
    copy_right = [43, 690, 560, 827]
    page_index = [290, 36, 326, 56]
    pdf_document = fitz.open(input_pdf)
    for i in range(0, pdf_document.page_count):
        page = pdf_document.load_page(i)
        page.draw_rect(info, color=(1, 1, 1), fill = (1, 1, 1))
        page.draw_rect(page_index, color=(1, 1, 1), fill = (1, 1, 1))
        if i == pdf_document.page_count - 1:
            page.draw_rect(copy_right, color=(1, 1, 1), fill = (1, 1, 1))
    pdf_document.save(output_pdf)

def with_margin(infopage):
    region = np.array(infopage)[69 : 207, 95 : 695]
    return not np.all(region == 255) # If all white -> no margin

if __name__ == "__main__":
    page0 = convert_from_path(sys.argv[1])[0]

    if with_margin(page0):
        print("with margin!")
        cover_pdf_area_withmargin(sys.argv[1], sys.argv[1].replace('.pdf', '_processed.pdf'))
    else:
        print("no margin")
        cover_pdf_area_withoutmargin(sys.argv[1], sys.argv[1].replace('.pdf', '_processed.pdf'))

    reader = PdfReader(sys.argv[1].replace('.pdf', '_processed.pdf'))
    output = PdfWriter()

    for i in range(1, len(reader.pages)): # Skip information page
        page = reader.pages[i]
        text = page.extract_text()
        if text.find("BLANK PAGE") == -1:
            p = reader.pages[i]
            output.add_page(p)
    reader.close()
    
    with open(sys.argv[1].replace('.pdf', '_processed.pdf'), 'wb') as f:
        output.write(f)

# TODO
# Something is wrong with the w24 series, the displacement is incorrect so must be handled separately