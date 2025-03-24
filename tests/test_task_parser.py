import os
import pytest
from ohcrn_lei.task import Task
from ohcrn_lei.task_parser import load_task, split_sections


# A dummy print_usage function to be passed to load_task,
# which will track whether it's been called or not.
class DummyUsage:
  def __init__(self):
    self.called = False

  def __call__(self):
    self.called = True


# Helper: create a temporary file with the given contents.
@pytest.fixture
def temp_task_file(tmp_path):
  def _create(contents: str) -> str:
    file_path = tmp_path / "task.txt"
    file_path.write_text(contents, encoding="utf-8")
    return str(file_path)

  return _create


# --- Tests for split_sections ---


def test_split_sections_valid():
  contents = (
    "##### START PROMPT #####\n"
    "This is the prompt text.\n"
    "It spans multiple lines.\n"
    "##### END PROMPT #####\n"
    "##### START PLUGINS #####\n"
    "plugin1=trie_hgnc\n"
    "plugin2=regex_hgvsg\n"
    "##### END PLUGINS #####"
  )
  sections = split_sections(contents)
  assert "PROMPT" in sections
  assert "PLUGINS" in sections
  expected_prompt = "This is the prompt text.\nIt spans multiple lines."
  expected_plugins = "plugin1=trie_hgnc\nplugin2=regex_hgvsg"
  assert sections["PROMPT"] == expected_prompt
  assert sections["PLUGINS"] == expected_plugins


def test_split_sections_nested_error():
  contents = (
    "##### START PROMPT #####\n"
    "Hello\n"
    "##### START PLUGINS #####\n"
    "plugin1=trie_hgnc\n"
    "##### END PROMPT #####\n"
    "##### END PLUGINS #####"
  )
  with pytest.raises(ValueError, match="Nested or overlapping sections not allowed"):
    split_sections(contents)


def test_split_sections_mismatched_end():
  contents = "##### START PROMPT #####\nHello\n##### END PLUGINS #####"
  with pytest.raises(ValueError, match="Mismatched section end found"):
    split_sections(contents)


def test_split_sections_unclosed_section():
  contents = "##### START PROMPT #####\nHello\n"
  with pytest.raises(ValueError, match="File ended without closing section"):
    split_sections(contents)


# --- Tests for load_task ---


def test_load_task_external_file_success(temp_task_file):
  # Build a valid task file for external file.
  file_contents = (
    "##### START PROMPT #####\n"
    "External file prompt text\n"
    "##### END PROMPT #####\n"
    "##### START PLUGINS #####\n"
    "pluginA=trie_hgnc\n"
    "pluginB=regex_hgvsg\n"
    "##### END PLUGINS #####"
  )
  file_path = temp_task_file(file_contents)

  dummy_usage = DummyUsage()
  # To avoid unwanted prints, you may monkeypatch print if desired.
  task_obj = load_task(file_path, dummy_usage)

  # Verify that the returned object is a Task with the expected prompt.
  assert isinstance(task_obj, Task)
  assert "External file prompt text" in str(task_obj)
  # Verify that plugins were set.
  expected_plugins = {"pluginA": "trie_hgnc", "pluginB": "regex_hgvsg"}
  # For comparison, use the __str__ output.
  assert str(expected_plugins) in str(task_obj)
  # Ensure print_usage was not called.
  assert not dummy_usage.called


def test_load_task_external_file_not_found(tmp_path):
  non_existent_file = str(tmp_path / "nonexistent.txt")
  dummy_usage = DummyUsage()

  # Capture printed output if desired.
  with pytest.raises(SystemExit) as se:
    load_task(non_existent_file, dummy_usage)
  # Expect exit with os.EX_NOTFOUND.
  assert se.value.code == os.EX_IOERR
  # Also, dummy_usage should have been called.
  assert dummy_usage.called


def test_load_task_internal_file_success(monkeypatch, tmp_path):
  dummy_usage = DummyUsage()
  task_obj = load_task("report", dummy_usage)
  assert isinstance(task_obj, Task)
  assert "Overview" in str(task_obj)
  assert not dummy_usage.called


def test_load_task_unknown_task(monkeypatch, tmp_path):
  """
  Test that if no task is found (external or internal), the function prints an error,
  calls print_usage, and exits with os.EX_USAGE.
  """
  dummy_usage = DummyUsage()
  # Use a task name that does not end with .txt and will not be found in package data.
  with pytest.raises(SystemExit) as se:
    load_task("nonexistent_task", dummy_usage)
  assert se.value.code == os.EX_USAGE
  assert dummy_usage.called


def test_load_task_invalid_plugin_definition(temp_task_file):
  """
  Test that a plugin line without an '=' operator triggers sys.exit with os.EX_USAGE.
  """
  file_contents = (
    "##### START PROMPT #####\n"
    "Some prompt\n"
    "##### END PROMPT #####\n"
    "##### START PLUGINS #####\n"
    "badplugindefinition\n"  # Missing '=' here.
    "##### END PLUGINS #####"
  )
  file_path = temp_task_file(file_contents)
  dummy_usage = DummyUsage()
  with pytest.raises(SystemExit) as se:
    load_task(file_path, dummy_usage)
  # Expect exit with os.EX_USAGE.
  assert se.value.code == os.EX_USAGE
  assert not dummy_usage.called


def test_load_task_invalid_format(temp_task_file):
  """
  Test a file that does not split into sections correctly,
  which should cause a ValueError in split_sections and then sys.exit with os.EX_NOTFOUND.
  """
  file_contents = "This file does not use section delimiters properly."
  file_path = temp_task_file(file_contents)
  dummy_usage = DummyUsage()
  with pytest.raises(SystemExit) as se:
    load_task(file_path, dummy_usage)
  assert se.value.code == os.EX_USAGE
  assert not dummy_usage.called
