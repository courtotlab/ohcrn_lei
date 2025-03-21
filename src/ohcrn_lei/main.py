import argparse
from ohcrn_lei import task_parser

def start() -> None:
  parser = argparse.ArgumentParser(
    description="Extract data from report file."
  )
  parser.add_argument('--no-ocr', action='store_true', help="Disable OCR processing.")
  parser.add_argument('--task', type=str, default='report', help="Specify the extraction task")
  parser.add_argument('filename', type=str, help="Path to the file to process.")
  args = parser.parse_args()
  
  # Output the parsed arguments
  print("OCR Disabled:" if args.no_ocr else "OCR Enabled")
  print("Task set to:", args.task)
  print("Processing file:", args.filename)

  task = task_parser.load_task(args.task)
  print(task)


    
if __name__ == '__main__':
  start()
