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
import sys
from importlib import metadata

import dotenv

from ohcrn_lei import task_parser
from ohcrn_lei.cli import (
  die,
  get_dotenv_file,
  is_poppler_installed,
  link,
  process_cli_args,
  prompt_for_api_key,
)


def start() -> None:
  """Main entry point for ohcrn-lei."""
  # print license header
  print(
    f"""
🌺🌺🌺 OHCRN-LEI 🌺🌺🌺 v{metadata.version("ohcrn_lei")}
Copyright © 2025  Ontario Institute for Cancer Research
This program comes with ABSOLUTELY NO WARRANTY.
This is free software, and you are welcome to redistribute it
under certain conditions. {link("https://www.gnu.org/licenses/gpl-3.0.txt", "See license for details")}.
"""
  )

  # parse command line arguments
  cli_parser, args = process_cli_args()

  # Output the parsed arguments
  print("Processing file:", args.filename)
  print(" * Task:", args.task)
  if args.mock_LLM:
    print(" * Using mock LLM output")

  # check if the file is a text file, if so, enable no-ocr mode
  if args.filename.endswith(".txt"):
    args.no_ocr = True

  if args.no_ocr:
    print(" * OCR disabled")
    # check that the file isn't a PDF file
    if args.filename.endswith(".pdf"):
      die("When using --no-ocr, the input file cannot be a PDF!", os.EX_USAGE)
  elif not is_poppler_installed():
    die("Poppler is not installed! Please install Poppler to process PDF files.")

  # check that file can be read
  if not os.access(args.filename, os.R_OK):
    die(f"File {args.filename} does not exist or cannot be read!", os.EX_IOERR)

  # check that API key is available
  dotenv_file = get_dotenv_file()
  dotenv.load_dotenv(dotenv_file)
  if "OPENAI_API_KEY" not in os.environ:
    print("\n⚠️ No API key found for OpenAI account!")
    prompt_for_api_key()
    # reload environment after key was saved
    dotenv.load_dotenv(dotenv_file)

  # Load the appropriate task. Pass print_usage as a lambda function for the task loader to use
  task = task_parser.load_task(args.task, lambda: cli_parser.print_usage())
  output = task.run(
    args.filename,
    chunk_size=args.page_batch,
    no_ocr=args.no_ocr,
    llm_mock=args.mock_LLM,
  )

  if args.outfile == "-" or args.outfile == "stdout":
    print("\nResult output:\n")
    json.dump(output, sys.stdout, indent=2)
  else:
    try:
      with open(args.outfile, "w") as fp:
        json.dump(output, fp, indent=2)
    except Exception as e:
      die(f"Unable to write output file {args.outfile}.\n{e}", os.EX_IOERR)
    else:
      print(f"Output successfully written to {args.outfile}")


if __name__ == "__main__":
  start()
