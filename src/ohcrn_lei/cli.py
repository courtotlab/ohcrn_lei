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
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

import dotenv


# helper function to exit with error message
def die(msg: str, code=1) -> None:
  """Prints a message to stderr and exits the program with the given code

  Args:
    msg: message to print
    code: exit code

  """
  print("❌ ERROR: " + msg, file=sys.stderr)
  sys.exit(code)


def get_dotenv_file() -> Path:
  """gets the path to the dotenv file

  Returns:
    The path to the dotenv file.
  """
  # ~/.config/ is the XDG standard for configuration file storage
  home = os.getenv("HOME")
  if home is None:
    die("Unable to find home directory!", os.EX_CONFIG)
  dotenv_dir = Path(str(home)) / ".config" / "ohcrn-lei"
  # if the directory doesn't exist: Create it.
  dotenv_dir.mkdir(parents=True, exist_ok=True)
  dotenv_file = dotenv_dir / ".env"
  return dotenv_file


def prompt_for_api_key() -> None:
  """Prompts the user for an OpenAI API key and saves it in dotenv."""
  dotenv_file = get_dotenv_file()

  key = input("Please enter your key: ").strip()
  if not key.startswith("sk-"):
    die("The provided strings is not a valide OpenAI API key!", os.EX_CONFIG)
  else:
    dotenv.set_key(dotenv_file, "OPENAI_API_KEY", key)
    print(f"Key was saved to {dotenv_file}")


def process_cli_args() -> tuple[ArgumentParser, Namespace]:
  """Processes the command line arguments

  Returns:
    A tuple containing the argument parser object and a dictionary of the arguments by name

  """
  parser = ArgumentParser(description="Extract data from report file.")
  parser.add_argument(
    "-b",
    "--page-batch",
    type=int,
    default=2,
    help="Number of pages to be processed at a given time. Default=2",
  )
  parser.add_argument(
    "-t",
    "--task",
    type=str,
    default="report",
    help="Specify the extraction task. This can either be a "
    "pre-defined task ('report','molecular_test','variant')"
    "or a plain *.txt file with a task definition. See documentation"
    "for the task definition file format specification."
    "Default: report",
  )
  parser.add_argument(
    "-o",
    "--outfile",
    type=str,
    default="-",
    help="Output file or '-' for stdout (default)",
  )
  parser.add_argument(
    "--mock-LLM",
    action="store_true",
    help="Don't make real LLM call, produce mock output instead.",
  )
  parser.add_argument("--no-ocr", action="store_true", help="Disable OCR processing.")
  parser.add_argument("filename", type=str, help="Path to the report file to process.")
  args = parser.parse_args()
  return parser, args
