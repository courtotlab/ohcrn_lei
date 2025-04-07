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

import os
from pathlib import Path

import dotenv
import pytest

from ohcrn_lei.cli import get_dotenv_file, process_cli_args, prompt_for_api_key


def test_process_cli_args_noArgs():
  with pytest.raises(SystemExit):
    process_cli_args()


def test_process_cli_args(monkeypatch):
  fake_args = ["ohcrn-lei", "-t", "test", "-o", "testout.json", "testfile.txt"]
  monkeypatch.setattr("argparse._sys.argv", fake_args)
  _, args = process_cli_args()
  assert args.task == "test"
  assert args.filename == "testfile.txt"
  assert args.page_batch == 2
  assert args.outfile == "testout.json"


def test_get_dotenv_file():
  file_path = Path(os.getenv("HOME")) / ".config" / "ohcrn-lei" / ".env"
  assert get_dotenv_file() == file_path


def test_prompt_for_api_key(monkeypatch, tmp_path):
  dotenv_file = tmp_path / ".env"
  fake_key = "sk-test"
  monkeypatch.setattr("builtins.input", lambda text: fake_key)
  monkeypatch.setattr("ohcrn_lei.cli.get_dotenv_file", lambda: dotenv_file)
  prompt_for_api_key()
  dotenv.load_dotenv(dotenv_file, override=True)
  assert os.getenv("OPENAI_API_KEY") == fake_key
