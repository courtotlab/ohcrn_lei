import importlib.resources
import re
import os
import sys
from ohcrn_lei.task import Task

def load_task(taskname, print_usage) -> Task:
  """
  Load a task by name. The name can either be
  an internal task (stored in package data), or an
  external file
  """

  taskData = ""
  #check if task refers to an external task file and if so, load it
  if re.search(r'\.txt$',taskname):
    try:
      with open(taskname, 'r', encoding='utf-8') as tin:
        taskData = tin.read()
    except Exception as e:
      print(f"ERROR: Task argument looks like a file, but that file cannot be found or read: {e}")
      print_usage()
      sys.exit(os.EX_NOTFOUND)
    
  #otherwise try to load interal task file
  else:
    resource_dir = importlib.resources.files("ohcrn_lei") / 'data'
    taskfiles = [f for f in resource_dir.iterdir() if f.is_file() and "_task.txt" in f.name]
    for tf in taskfiles:
      if taskname in tf.name:
        taskData = tf.read_text()

  if not taskData:
    print(f"ERROR: Unknown task {taskname}")
    print_usage()
    sys.exit(os.EX_USAGE)

  try:
    task_sections = split_sections(taskData)
  except ValueError as e:
      print(f"ERROR: Invalid task file format: {e}")
      sys.exit(os.EX_NOTFOUND)

  task = Task(task_sections['PROMPT'])

  if 'PLUGINS' in task_sections:
    plugins = {}
    for line in task_sections['PLUGINS'].splitlines():
      fields=line.split("=")
      if len(fields) != 2:
        print(f"ERROR: Invalid plugin definition {line} in task {taskname}")
        sys.exit(os.EX_USAGE)
      # out.update({'key':fields[0], 'op':fields[1]})
      plugins[fields[0]] = fields[1]
    task.set_plugins(plugins)
     
  return task


def split_sections(contents):
    # Regex pattern to match section delimiters.
    # It matches either START or END followed by a section name.
    pattern = re.compile(r"#####\s*(START|END)\s+([A-Z0-9_]+)\s*#####", re.I)
    
    sections = {}
    current_section = None
    content_lines = []

    for line in contents.splitlines():
        # Check if the line matches our section delimiter pattern.
        match = pattern.match(line.strip())
        if match:
            directive, section_name = match.groups()
            directive = directive.upper()
            section_name = section_name.upper()
            if directive == "START":
                # If we're already in a section, you might want to raise an error or handle nested sections.
                if current_section is not None:
                    raise ValueError(f"Nested or overlapping sections not allowed. Already in section: {current_section}")
                # Start a new section
                current_section = section_name
                content_lines = []
            elif directive == "END":
                if current_section != section_name:
                    raise ValueError(f"Mismatched section end found. Expected end for '{current_section}', but got end for '{section_name}'.")
                # End the current section and store its content.
                sections[current_section] = "\n".join(content_lines).strip()
                current_section = None
                content_lines = []
            continue  # Skip processing the delimiter lines
        
        # If we're inside a section, accumulate the lines.
        if current_section is not None:
            content_lines.append(line)
    
    # Optionally, you can check if the file ended while still in a section
    if current_section is not None:
        raise ValueError(f"File ended without closing section '{current_section}'.")
    
    return sections
