import argparse
import json
from ohcrn_lei import task_parser
import os
import sys

def start() -> None:
  parser = argparse.ArgumentParser(
    description="Extract data from report file."
  )
  parser.add_argument('--no-ocr', action='store_true', 
    help="Disable OCR processing."
  )
  parser.add_argument('-t','--task', type=str, default='report', 
    help="Specify the extraction task. This can either be a "
    "pre-defined task ('report','molecular_test','variant')"
    "or a plain *.txt file with a task definition. See documentation"
    "for the task definition file format specification."
    "Default: report"
  )
  parser.add_argument('-o','--outfile', type=str, default='-',
    help="Output file or '-' for stdout (default)"
  )
  parser.add_argument('filename', type=str, 
    help="Path to the report file to process."
  )
  args = parser.parse_args()
  
  # Output the parsed arguments
  print("OCR Disabled:" if args.no_ocr else "OCR Enabled")
  print("Task set to:", args.task)
  print("Processing file:", args.filename)

  #check that file can be read
  if not os.access(args.filename, os.R_OK):
    print(f"ERROR: File {args.filename} does not exist or cannot be read!")
    sys.exit(os.EX_IOERR)

  # Wrap the print_usage call in a lambda function
  print_usage = lambda: parser.print_usage()

  task = task_parser.load_task(args.task, print_usage)
  output = task.run(args.filename)

  if args.outfile == "-" or args.outfile == "stdout":
    print(output)
  else:
    try:
      with open(args.outfile, 'w') as fp:
        json.dump(output, fp)
    except Exception as e:
      print(f"ERROR: Unable to write output file {args.outfile}.\n{e}")
      sys.exit(os.EX_IOERR)
    else:
      print(f"Output successfully written to {args.outfile}")


    
if __name__ == '__main__':
  start()
