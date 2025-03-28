import sys


# helper function to exit with error message
def die(msg, code=1):
  print("🛑 ERROR: " + msg, file=sys.stderr)
  sys.exit(code)
