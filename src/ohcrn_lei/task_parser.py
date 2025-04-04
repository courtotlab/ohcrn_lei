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

import importlib.resources
import os
import re
from typing import Callable, List

from ohcrn_lei.cli import die
from ohcrn_lei.task import Task


# HACK: Handle usage printing in cli.py somehow instead.
def load_task(taskname: str, print_usage: Callable[[], None]) -> Task:
  """Load a task by name. The name can either be
  an internal task (stored in package data), or an
  external file.

  Args:
    taskname: the name of the task to load (internal name or file path)
    print_usage: A function that can be called to print usage information

  Returns:
    A task object

  """
  taskData = ""
  # check if task refers to an external task file and if so, load it
  if re.search(r"\.txt$", taskname):
    try:
      with open(taskname, "r", encoding="utf-8") as tin:
        taskData = tin.read()
    except Exception as e:
      print_usage()
      die(
        f"Task argument looks like a file, but that file cannot be found or read: {e}",
        os.EX_IOERR,
      )

  # otherwise try to load interal task file
  else:
    resource_dir = importlib.resources.files("ohcrn_lei") / "data"
    taskfiles = [
      f for f in resource_dir.iterdir() if f.is_file() and "_task.txt" in f.name
    ]
    for tf in taskfiles:
      if taskname in tf.name:
        taskData = tf.read_text()

  if not taskData:
    print_usage()
    die(f"Unknown task {taskname}", os.EX_USAGE)

  try:
    task_sections = split_sections(taskData)
  except ValueError as e:
    die(f"Invalid task file format: {e}", os.EX_USAGE)

  if "PROMPT" not in task_sections:
    die("Invalid task file format: No prompt section.", os.EX_USAGE)

  task = Task(task_sections["PROMPT"])

  if "PLUGINS" in task_sections:
    plugins = {}
    for line in task_sections["PLUGINS"].splitlines():
      fields = line.split("=")
      if len(fields) != 2:
        die(f"Invalid plugin definition {line} in task {taskname}", os.EX_USAGE)
      # plugins[fields[0]] = fields[1]
      plugins.update({fields[0]: fields[1]})
    task.set_plugins(plugins)

  return task


def split_sections(contents: str) -> dict[str, str]:
  """Splits text according to content sections, which are delimited by lines like:
  ##### START FOOBAR #####
  text here
  ##### END FOOBAR #####

  Args:
    contents: The input text string

  Returns:
    A dictionary linking section names to section content

  Raises:
    ValueError: if the content does not conform to the above format.

  """
  # Regex pattern to match section delimiters.
  # It matches either START or END followed by a section name.
  pattern = re.compile(r"#####\s*(START|END)\s+([A-Z0-9_]+)\s*#####", re.I)

  sections = {}
  current_section = None
  content_lines: List[str] = []

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
          raise ValueError(
            f"Nested or overlapping sections not allowed. Already in section: {current_section}"
          )
        # Start a new section
        current_section = section_name
        content_lines = []
      elif directive == "END":
        if current_section != section_name:
          raise ValueError(
            f"Mismatched section end found. Expected end for '{current_section}', but got end for '{section_name}'."
          )
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
