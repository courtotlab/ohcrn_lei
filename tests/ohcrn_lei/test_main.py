"""OHCRN-LEI - LLM-based Extraction of Information
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

import json
import os

import pytest

from ohcrn_lei.main import start


def test_start(monkeypatch, tmp_path):
  tmpfile = tmp_path / "input.txt"
  tmpfile.write_text("This is an example text")
  fake_args = ["ohcrn-lei", "-t", "report", "--mock-LLM", "--no-ocr", str(tmpfile)]
  monkeypatch.setattr("argparse._sys.argv", fake_args)
  start()


def test_start_with_outfile(monkeypatch, tmp_path):
  tmpfile = tmp_path / "input.txt"
  tmpfile.write_text("This is an example text")
  outfile = tmp_path / "outfile.json"
  fake_args = [
    "ohcrn-lei",
    "-t",
    "report",
    "-o",
    str(outfile),
    "--mock-LLM",
    "--no-ocr",
    str(tmpfile),
  ]
  monkeypatch.setattr("argparse._sys.argv", fake_args)
  start()
  outjson = json.loads(outfile.read_text())
  assert outjson["Pages 1-2"]["output"] == "mock"


def test_start_no_file_error(monkeypatch):
  fake_args = ["ohcrn-lei", "-t", "report", "--mock-LLM", "--no-ocr", "testfile.txt"]
  monkeypatch.setattr("argparse._sys.argv", fake_args)
  with pytest.raises(SystemExit) as e:
    start()
  assert e.value.code == os.EX_IOERR
