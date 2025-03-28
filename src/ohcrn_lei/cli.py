import argparse
import sys


# helper function to exit with error message
def die(msg, code=1):
  print("🛑 ERROR: " + msg, file=sys.stderr)
  sys.exit(code)


def process_cli_args():
  parser = argparse.ArgumentParser(description="Extract data from report file.")
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
