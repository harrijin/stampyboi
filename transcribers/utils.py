import os
import requests
import PyPDF2
import re

"""
Extracts text from pdf file

source - String of URL of PDF file
"""
def get_pdf_text(source):
    
    req = requests.get(source, stream=True)

    # Use a stream to download the PDF file
    with open("temp.pdf", "wb") as pdf:
        for chunk in req.iter_content(chunk_size=1024):
            if chunk:
                pdf.write(chunk)
    
    file_read = PyPDF2.PdfFileReader('temp.pdf')
    num_pages = file_read.getNumPages()

    # Delete temp PDF file used to extract text
    os.remove('temp.pdf')

    regex = re.compile(r'[\n\r\t]')
    
    return ''.join(regex.sub('', file_read.getPage(page_num).extractText()) for page_num in range(num_pages))
