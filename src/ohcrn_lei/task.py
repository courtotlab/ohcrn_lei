import os
import sys

from ohcrn_lei import llm_calls
from ohcrn_lei.extractHGNCSymbols import find_HGNC_symbols
from ohcrn_lei.regex_utils import get_coding_changes
from ohcrn_lei.regex_utils import get_genomic_changes
from ohcrn_lei.regex_utils import get_protein_changes
from ohcrn_lei.regex_utils import get_variant_ids
from ohcrn_lei.regex_utils import get_chromosomes


class Task:
  """
  Task performs an extraction task. It gets configured with an
  LLM prompt and option al plugins.

  run() executes the task on a given input file.
  """

  def __init__(self, prompt: str):
    """
    Constructor to create a new task with an LLM prompt.
    """
    self.prompt = prompt
    self.plugins = None

  def set_plugins(self, plugins: dict):
    """
    Sets the plugins for this task. Plugins are formatted
    as dicts with have the desired json key as keys and
    the desired operations as values.
    """
    self.plugins = plugins

  # print string representation override
  def __str__(self):
    return "PROMPT:\n" + self.prompt + "\nPLUGINS:\n" + str(self.plugins)

  def run(self, inputfile: str, chunk_size=2, llm_mock=False) -> dict:
    """
    Run the task on the given input file. If the file has multiple
    pages use the chunk size to determine how many pages are processed
    in a single batch.
    """
    # TODO: add OCR
    try:
      with open(inputfile, "r", encoding="utf-8") as instream:
        text = instream.read()
    except Exception as e:
      print(f"ERROR: Unable to read file {inputfile}: {e}")
      sys.exit(os.EX_IOERR)

    # simulate multiple pages for plain text input
    all_text = [text]

    i = 0
    full_results = {}

    while i <= len(all_text) - (chunk_size - 1):
      print("Sending request for pages", i, "to", i + chunk_size - 1)
      pages_text = " ".join(all_text[i : i + chunk_size])

      # Prepare query
      query_msg = (
        "Use the given format to extract information from the following input: "
        + pages_text
      )
      # Call the API to get JSON (dict) with the requested fields in the prompt
      llm_results = llm_calls.call_gpt_api(self.prompt, query_msg, "gpt-4o", llm_mock)
      # Add to llm dict
      page_key = "Pages " + str(i + 1) + "-" + str(i + chunk_size)
      full_results[page_key] = llm_results

      # Run plugins
      if self.plugins:
        for path, plugin_name in self.plugins.items():
          match plugin_name:
            case "trie_hgnc":
              pl_output = find_HGNC_symbols(pages_text)
            case "regex_hgvsg":
              pl_output = get_genomic_changes(pages_text)
            case "regex_hgvsc":
              pl_output = get_coding_changes(pages_text)
            case "regex_hgvsp":
              pl_output = get_protein_changes(pages_text)
            case "regex_variants":
              pl_output = get_variant_ids(pages_text)
            case "regex_chromosome":
              pl_output = get_chromosomes(pages_text)
            case _:
              raise ValueError(f"Unrecognized plugin name: {plugin_name}")
          # add or replace
          full_results[page_key].update({path: pl_output})

      i += chunk_size

    return full_results
