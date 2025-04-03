"""
OHCRN-LEI - LLM-based Extraction of Information
Copyright (C) 2025 Ontario Institute for Cancer Research

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import os
from typing import List

import easyocr  # type: ignore
import numpy as np
from pdf2image import convert_from_path

from ohcrn_lei.cli import die


def convert_pdf_to_str_list(pdf_path: str, language_list=["en"], dpi=300) -> List[str]:
  """
  Use EasyOCR to convert the given PDF file into plain text but page by page.
  Returns a list of strings representing each page.

  Args:
    pdf_path: path to the pdf input file
    language_list: A list of languages to detect for OCR
    dpi: The scan resolution to use for OCR

  Returns:
    A list of text strings representing the document pages
  """
  # Initialize the EasyOCR reader.
  reader = easyocr.Reader(language_list)

  # Convert PDF pages to images.
  try:
    # You can adjust dpi if necessary.
    pages = convert_from_path(pdf_path, dpi=dpi)
  except Exception as e:
    die(f"Failed to converting PDF to images: {e}", os.EX_CONFIG)

  full_text = []
  for i, page in enumerate(pages):
    print(f" - Processing page {i + 1}...")
    # Convert PIL image to numpy array.
    image_np = np.array(page)

    # Use EasyOCR to extract text from the image.
    try:
      results = reader.readtext(image_np, detail=0, paragraph=True)
      # Join text from detected regions.
      page_text = "\n".join(results)
      full_text.append(page_text)
    except Exception as e:
      die(f"Failed processing page {i + 1}: {e}", os.EX_DATAERR)

  return full_text


def convert_pdf_to_text(pdf_path: str, language_list=["en"], dpi=300) -> str:
  """
  Use EasyOCR to convert the given PDF file into plain text.
  Returns a string, with pages separated by two newline characters.

  Args:
    pdf_path: path to the pdf input file
    language_list: A list of languages to detect for OCR
    dpi: The scan resolution to use for OCR

  Returns:
    A text string of the OCR result.
  """
  pages = convert_pdf_to_str_list(pdf_path, language_list, dpi)
  return "\n\n".join(pages)


# if __name__ == "__main__":
#     # Specify the path to your PDF file
#     indir = '../input_docs/'
#     pdf_files = [indir+f for f in listdir(indir) if 'pdf' in str(f) and isfile(join(indir, f))]
#     for pdf_file in pdf_files:
#         extracted_text = extract_text_from_pdf(pdf_file)
#         output_file = indir+'ocr_out/'+re.sub(".pdf$",".txt",basename(pdf_file))
#         try:
#             with open(output_file, 'w', encoding='utf-8') as file:
#                 file.write(extracted_text)
#                 print(f"Extraction saved to {output_file}")
#         except Exception as e:
#             print(f"Error while writing file: {e}")
