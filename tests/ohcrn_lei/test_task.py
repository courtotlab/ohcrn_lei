"""
OHCRN-LEI - LLM-based Extraction of Information
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

import os

import pytest

from ohcrn_lei.task import Task

# Dummy data to return from our fake LLM call.
DUMMY_LLM_RESULT = {"result": "llm response"}

# Dummy results for fake plugins.
PLUGIN_RESULTS = {
  "trie_hgnc": ["BRCA1", "BRCA2"],
  "regex_hgvsg": ["g.123A>T"],
  "regex_hgvsc": ["c.456G>C"],
  "regex_hgvsp": ["p.Val78Met"],
  "regex_variants": ["rs1234"],
  "regex_chromosome": ["chr1", "chr2"],
}


# Fixtures for dummy llm_calls and plugins will be created using monkeypatch.
@pytest.fixture()
def fake_llm_calls(monkeypatch):
  # Create a fake llm_calls.call_gpt_api that always returns the dummy result.
  def fake_call_gpt_api(prompt, query_msg, model, llm_mock):
    return DUMMY_LLM_RESULT.copy()

  # Replace the function in the module path.
  monkeypatch.setattr("ohcrn_lei.task.call_gpt_api", fake_call_gpt_api)


@pytest.fixture()
def fake_plugins(monkeypatch):
  # For each plugin function, replace it with one that returns the preconfigured dummy data.
  monkeypatch.setattr(
    "ohcrn_lei.task.find_HGNC_symbols", lambda text: PLUGIN_RESULTS["trie_hgnc"]
  )
  monkeypatch.setattr(
    "ohcrn_lei.task.get_genomic_changes", lambda text: PLUGIN_RESULTS["regex_hgvsg"]
  )
  monkeypatch.setattr(
    "ohcrn_lei.task.get_coding_changes", lambda text: PLUGIN_RESULTS["regex_hgvsc"]
  )
  monkeypatch.setattr(
    "ohcrn_lei.task.get_protein_changes", lambda text: PLUGIN_RESULTS["regex_hgvsp"]
  )
  monkeypatch.setattr(
    "ohcrn_lei.task.get_variant_ids", lambda text: PLUGIN_RESULTS["regex_variants"]
  )
  monkeypatch.setattr(
    "ohcrn_lei.task.get_chromosomes", lambda text: PLUGIN_RESULTS["regex_chromosome"]
  )


@pytest.fixture()
def fake_pdf_convert(monkeypatch):
  def fake_convert_pdf_to_str_list(filename):
    return [
      "Page1 content.",
      "Page2 content with gene MTHFR.",
      "Page3 content with variant rs1234.",
    ]

  # import ohcrn_lei.pdf_to_text
  monkeypatch.setattr(
    "ohcrn_lei.task.convert_pdf_to_str_list", fake_convert_pdf_to_str_list
  )


def test_str_representation():
  prompt = "Extract info"
  task_obj = Task(prompt)
  plugins = {"plugin1": "trie_hgnc", "plugin2": "regex_hgvsg"}
  task_obj.set_plugins(plugins)
  result_str = str(task_obj)
  assert "PROMPT:" in result_str
  assert prompt in result_str
  assert "PLUGINS:" in result_str
  assert str(plugins) in result_str


def test_convert_txt_to_str_list_success(tmp_path):
  # Write a temporary text file
  content = "This is a test file.\nContains sample text."
  file_path = tmp_path / "testfile.txt"
  file_path.write_text(content, encoding="utf-8")

  task_obj = Task("dummy prompt")
  result = task_obj.convert_txt_to_str_list(str(file_path))
  # Since our implementation wraps the entire text into a single list element.
  assert isinstance(result, list)
  assert len(result) == 1
  assert result[0] == content


def test_run_no_ocr_without_plugins(tmp_path, fake_llm_calls):
  # Create a temporary text file with dummy content.
  content = "Page one text. Page two text."
  file_path = tmp_path / "file.txt"
  file_path.write_text(content, encoding="utf-8")

  prompt = "Please extract fields"
  task_obj = Task(prompt)
  # Do not set any plugins.

  # Run with no_ocr True so that convert_txt_to_str_list is used.
  # Set chunk_size to 1 so that each page (here only one element in list) is processed.
  result = task_obj.run(str(file_path), chunk_size=1, no_ocr=True, llm_mock=True)

  # Expect one batch with key "Pages 1-1"
  assert "Pages 1-1" in result
  # The llm results should be present as provided by our fake llm_calls.
  assert result["Pages 1-1"] == DUMMY_LLM_RESULT


def test_run_with_plugins(tmp_path, fake_llm_calls, fake_pdf_convert, fake_plugins):
  # This won't really be used. Will be ignored by monkeypatch rule
  file_path = str(tmp_path / "dummy.pdf")

  prompt = "Extract data"
  task_obj = Task(prompt)
  # Set plugins for several operations.
  plugins = {
    "hgnc_plugin": "trie_hgnc",
    "genomic_plugin": "regex_hgvsg",
    "coding_plugin": "regex_hgvsc",
    "protein_plugin": "regex_hgvsp",
    "variants_plugin": "regex_variants",
    "chromosomes_plugin": "regex_chromosome",
  }
  task_obj.set_plugins(plugins)

  # Run with OCR (default)
  result = task_obj.run(file_path, chunk_size=2, no_ocr=False, llm_mock=True)

  # We expect two chunks since we have three pages with chunk_size=2.
  expected_keys = ["Pages 1-2", "Pages 3-4"]
  for key in expected_keys:
    assert key in result
    # llm result data from our fake call plus plugin fields.
    res = result[key]
    # Check that all plugin keys are present.
    for plugin_key, plugin_name in plugins.items():
      # Our fake plugin functions simply return the preconfigured values.
      expected_plugin_value = PLUGIN_RESULTS[plugin_name]
      assert plugin_key in res
      assert res[plugin_key] == expected_plugin_value
    # Also, the dummy llm result should be present.
    assert res.get("result") == DUMMY_LLM_RESULT["result"]


def test_run_invalid_plugin(tmp_path):
  # Create a temporary text file.
  content = "Test content for invalid plugin."
  file_path = tmp_path / "input.txt"
  file_path.write_text(content, encoding="utf-8")

  prompt = "Extract something"
  task_obj = Task(prompt)
  # Set a plugin with an unrecognized name.
  plugins = {"bad_plugin": "unknown_plugin"}
  task_obj.set_plugins(plugins)

  with pytest.raises(ValueError, match="Unrecognized plugin name"):
    task_obj.run(str(file_path), chunk_size=1, no_ocr=True, llm_mock=True)


def test_read_file_failure(monkeypatch):
  # Test that if file reading fails the process calls sys.exit with os.EX_IOERR.
  prompt = "Test exit on file read error"
  task_obj = Task(prompt)

  # Monkeypatch open to always raise an IOError
  def fake_open(*args, **kwargs):
    raise IOError("Unable to open file")

  monkeypatch.setattr("builtins.open", fake_open)

  # Since convert_txt_to_str_list uses sys.exit, we want to catch the SystemExit.
  with pytest.raises(SystemExit) as excinfo:
    task_obj.convert_txt_to_str_list("nonexistent.txt")
  # Check that the exit code is os.EX_IOERR.
  assert excinfo.value.code == os.EX_IOERR
