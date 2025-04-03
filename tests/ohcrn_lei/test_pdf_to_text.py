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
import pytest
from ohcrn_lei.pdf_to_text import (convert_pdf_to_str_list, convert_pdf_to_text)

FAKE_TEXT = "This is a fake text."

# Fixtures for dummy calls to pdf2image and EasyOCR
@pytest.fixture()
def fake_calls(monkeypatch):
  # Create a fake pdf2image call that creates an list of lists of numbers
  #which should be passable to the numpy array later
  def fake_convert_from_path(pdf_path, dpi):
    return [[1,2,3,4],[5,6,7,8]]
  
  monkeypatch.setattr("ohcrn_lei.pdf_to_text.convert_from_path", fake_convert_from_path)

  #Also patch out the call to EasyOCR
  class FakeReader:
    def __init__(self, language_list):
      pass

    def readtext(self,image_np, detail, paragraph):
      return [FAKE_TEXT]
  
  monkeypatch.setattr("ohcrn_lei.pdf_to_text.easyocr.Reader",FakeReader)


def test_conver_pdf_to_str_list(fake_calls, tmp_path):
  pages = convert_pdf_to_str_list(tmp_path/"test.pdf")
  for page in pages:
    assert page == FAKE_TEXT

def test_conver_pdf_to_text(fake_calls, tmp_path):
  output = convert_pdf_to_text(tmp_path/"test.pdf")
  expected = FAKE_TEXT + "\n\n" + FAKE_TEXT
  assert output == expected
  
### Test Error in EasyOCR

# Fixtures for dummy calls to pdf2image and EasyOCR
@pytest.fixture()
def fake_calls_OCR_Exception(monkeypatch):
  # Create a fake pdf2image call that creates an list of lists of numbers
  #which should be passable to the numpy array later
  def fake_convert_from_path(pdf_path, dpi):
    return [[1,2,3,4],[5,6,7,8]]
  
  monkeypatch.setattr("ohcrn_lei.pdf_to_text.convert_from_path", fake_convert_from_path)

  #Also patch out the call to EasyOCR
  class FakeReader:
    def __init__(self, language_list):
      pass

    def readtext(self,image_np, detail, paragraph):
      raise Exception("Fake exception")
  
  monkeypatch.setattr("ohcrn_lei.pdf_to_text.easyocr.Reader",FakeReader)

def test_conver_pdf_to_text_OCR_Error(fake_calls_OCR_Exception, tmp_path):
  with pytest.raises(SystemExit) as e:
    convert_pdf_to_text(tmp_path/"test.pdf")
  assert e.value.code == os.EX_DATAERR

### Test Error in pdf2text

# Fixtures for dummy calls to pdf2image and EasyOCR
@pytest.fixture()
def fake_calls_PDF_Exception(monkeypatch):
  # Create a fake pdf2image call that creates an list of lists of numbers
  #which should be passable to the numpy array later
  def fake_convert_from_path(pdf_path, dpi):
      raise Exception("Fake exception")
  
  monkeypatch.setattr("ohcrn_lei.pdf_to_text.convert_from_path", fake_convert_from_path)

  #Also patch out the call to EasyOCR
  class FakeReader:
    def __init__(self, language_list):
      pass

    def readtext(self,image_np, detail, paragraph):
      return [FAKE_TEXT]
  
  monkeypatch.setattr("ohcrn_lei.pdf_to_text.easyocr.Reader",FakeReader)

def test_conver_pdf_to_text_PDF_Error(fake_calls_PDF_Exception, tmp_path):
  with pytest.raises(SystemExit) as e:
    convert_pdf_to_text(tmp_path/"test.pdf")
  assert e.value.code == os.EX_CONFIG
  