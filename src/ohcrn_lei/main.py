import json
import os

from ohcrn_lei import task_parser
from ohcrn_lei.cli import die, process_cli_args


def start() -> None:
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
    # check that the file isn't a PDF file
    if args.filename.endswith(".pdf"):
      die("When using --no-ocr, the input file cannot be a PDF!", os.EX_USAGE)
    print(" * OCR disabled")

  # check that file can be read
  if not os.access(args.filename, os.R_OK):
    die(f"File {args.filename} does not exist or cannot be read!", os.EX_IOERR)

  # Load the appropriate task. Pass print_usage as a lambda function for the task loader to use
  task = task_parser.load_task(args.task, lambda: cli_parser.print_usage())
  output = task.run(
    args.filename,
    chunk_size=args.page_batch,
    no_ocr=args.no_ocr,
    llm_mock=args.mock_LLM,
  )

  if args.outfile == "-" or args.outfile == "stdout":
    print(output)
  else:
    try:
      with open(args.outfile, "w") as fp:
        # TODO: Look into pretty-print https://stackoverflow.com/questions/12943819/how-to-prettyprint-a-json-file
        json.dump(output, fp)
    except Exception as e:
      die(f"Unable to write output file {args.outfile}.\n{e}", os.EX_IOERR)
    else:
      print(f"Output successfully written to {args.outfile}")


if __name__ == "__main__":
  start()
