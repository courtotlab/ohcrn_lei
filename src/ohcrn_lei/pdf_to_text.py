import tempfile
from typing import List
import fitz
import easyocr


def convert_pdf_to_text(pdf_file_path: str) -> str:
  doc = fitz.open(pdf_file_path)

  zoom = 4
  mat = fitz.Matrix(zoom, zoom)

  reader = easyocr.Reader(["en"])

  # List to store OCR results from all pages
  all_text = ""

  # Loop through each page in the PDF
  for i in range(len(doc)):
    val = f"image_{i + 1}.png"

    # Convert page to image
    page = doc.load_page(i)
    pix = page.get_pixmap(matrix=mat)
    pix.save(val)

    # Read text from the image
    result = reader.readtext(val, detail=0)
    all_text += "\n".join(result) + "\n"

  doc.close()

  return all_text


def convert_pdf_to_str_list(pdf_file_path: str) -> List[str]:
  doc = fitz.open(pdf_file_path)

  zoom = 4
  mat = fitz.Matrix(zoom, zoom)

  reader = easyocr.Reader(["en"])

  # List to store OCR results from all pages
  pages_txt = []

  # Loop through each page in the PDF
  with tempfile.TemporaryDirectory() as tmpdirname:
    for i in range(len(doc)):
      val = f"{tmpdirname}/image_{i + 1}.png"

      # Convert page to image
      page = doc.load_page(i)
      pix = page.get_pixmap(matrix=mat)
      pix.save(val)

      # Read text from the image
      result = reader.readtext(val, detail=0)
      pages_txt.append("\n".join(result))

  doc.close()

  return pages_txt
