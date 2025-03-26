import argparse
import json
from ohcrn_lei import task_parser
import os
import sys


# helper function to exit with error message
def die(msg, code=1):
  print("ERROR: " + msg, file=sys.stderr)
  sys.exit(code)


def start() -> None:
  parser = argparse.ArgumentParser(description="Extract data from report file.")
  parser.add_argument("--no-ocr", action="store_true", help="Disable OCR processing.")
  parser.add_argument(
    "--mock-LLM",
    action="store_true",
    help="Don't make real LLM call, produce mock output instead.",
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
  parser.add_argument("filename", type=str, help="Path to the report file to process.")
  args = parser.parse_args()

  # Output the parsed arguments
  print("Processing file:", args.filename)
  print(" * Task:", args.task)
  if args.mock_LLM:
    print(" * Using mock LLM output")

  # check if the file is a text file, if so, enable no-ocr mode
  if args.filename.endswith(".txt"):
    args.no_ocr = True

  if args.no_ocr:
    # check that the file isn't a PDF file
    if args.filename.endswith(".pdf"):
      die("When using --no-ocr, the input file cannot be a PDF!", os.EX_USAGE)
    print(" * OCR disabled")

  # check that file can be read
  if not os.access(args.filename, os.R_OK):
    die(f"ERROR: File {args.filename} does not exist or cannot be read!", os.EX_IOERR)

  # Wrap the print_usage call in a lambda function
  task = task_parser.load_task(args.task, lambda: parser.print_usage())
  output = task.run(
    args.filename, chunk_size=2, no_ocr=args.no_ocr, llm_mock=args.mock_LLM
  )

  if args.outfile == "-" or args.outfile == "stdout":
    print(output)
  else:
    try:
      with open(args.outfile, "w") as fp:
        json.dump(output, fp)
    except Exception as e:
      die(f"ERROR: Unable to write output file {args.outfile}.\n{e}", os.EX_IOERR)
    else:
      print(f"Output successfully written to {args.outfile}")


if __name__ == "__main__":
  start()
