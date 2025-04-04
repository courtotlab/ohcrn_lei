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

import io

import pytest
import requests

from ohcrn_lei.extractHGNCSymbols import (
  eliminate_submatches,
  filterAliases,
  find_HGNC_symbols,
  load_or_build_Trie,
  parse_HGNC_from_URL,
)
from ohcrn_lei.trieSearch import Trie

# ----------------------------------------------------------------------
# Helpers / Mocks

FAKE_URL = "https://localhost/fakeURL"
GENES = ["MTHFR", "CHEK2", "UBE2I"]
TEST_TEXT = "We found variants in MTHFR, CHEK2 and UBE2I. NoMatch"
FAKE_TSV = (
  "hgnc_id\tsymbol\tcol3\tcol4\tcol5\tcol6\tcol7\tcol8\taliases\tcol10\tlegacy\n"
  'HGNC:1\tMTHFR\t-\t-\t-\t-\t-\t-\t\t-\t"NoMatch"\n'
  'HGNC:2\tCHEK2\t-\t-\t-\t-\t-\t-\t\t-\t"CHK2"\n'
  'HGNC:3\tUBC6\t-\t-\t-\t-\t-\t-\t"UBE2I|NoMatch"\t-\t\n'
  "HGNC:4\tBrokenLine"
)


class FakeResponse:
  def __init__(self, content, status_code=200):
    self.content = content
    self.status_code = status_code
    self._io = io.StringIO(content)

  def raise_for_status(self):
    if self.status_code != 200:
      raise requests.exceptions.HTTPError(f"Status code: {self.status_code}")

  def iter_lines(self, decode_unicode=False):
    # yield each line from the StringIO object. In real world lines don't include newline,
    # so strip them.
    self._io.seek(0)
    for line in self._io:
      yield line.rstrip("\n")

  def __enter__(self):
    return self

  def __exit__(self, *args):
    self._io.close()


def test_filterAliases_valid_and_invalid():
  # Valid alias must have length > 2 and at least one uppercase letter immediately followed by a number.
  valid = "A1B"  # has A1
  invalid_short = "A1"  # too short
  invalid_numerics = "abc"  # no uppercase followed by digit
  valid2 = "XYZ9"  # has Y9 or Z9
  aliases = [valid, invalid_short, invalid_numerics, valid2]
  expected = [valid, valid2]
  result = filterAliases(aliases)
  assert result == expected


# ----------------------------------------------------------------------
# Tests for parse_HGNC_from_URL


def test_parse_HGNC_from_URL(monkeypatch):
  # Create a fake response
  def fake_get(*args, **kwargs):
    return FakeResponse(FAKE_TSV)

  # monkeypatch.setattr(requests, "get", fake_get)
  monkeypatch.setattr("ohcrn_lei.extractHGNCSymbols.requests.get", fake_get)

  # Call the function. It will create a Trie and insert symbols.
  trie = parse_HGNC_from_URL(FAKE_URL)
  # Check that the official symbols are inserted.
  matches = trie.search_in_text(TEST_TEXT)
  found = {match for (_, match) in matches}
  for gene in GENES:
    assert gene in found


def test_parse_HGNC_from_URL_bad_response(monkeypatch):
  def fake_get(*args, **kwargs):
    return FakeResponse(None, status_code=404)

  monkeypatch.setattr("ohcrn_lei.extractHGNCSymbols.requests.get", fake_get)

  with pytest.raises(SystemExit):
    parse_HGNC_from_URL(FAKE_URL)


# ----------------------------------------------------------------------
# Tests for eliminate_submatches


def test_eliminate_submatches_no_submatches():
  # Provide matches that do not overlap as submatches.
  matches = [(0, "ABC"), (5, "DEF")]
  result = eliminate_submatches(matches)
  assert result == matches


def test_eliminate_submatches_with_submatches():
  # Create overlapping matches; e.g. match at index 0 is "CHEK2" and match at index 1 is "HE"
  matches = [(10, "CHEK2"), (11, "HE"), (20, "GENE")]
  # "HE" is fully inside "CHEK2", so should be removed.
  expected = [(10, "CHEK2"), (20, "GENE")]
  result = eliminate_submatches(matches)
  assert result == expected


def test_eliminate_submatches_multiple():
  # More complex scenario: overlapping intervals:
  # Matches: "TESTING" at pos 5, "TEST" at pos 5, "ING" at pos 9, and "STING" at pos 7.
  matches = [(5, "TESTING"), (5, "TEST"), (9, "ING"), (7, "STING")]
  # Here, "TEST" and "ING" are submatches of "TESTING" and "STING" respectively.
  expected = [(5, "TESTING")]
  result = eliminate_submatches(matches)
  # Since order might be preserved, check equivalence:
  assert sorted(result) == sorted(expected)


# ----------------------------------------------------------------------
# Tests for load_or_build_Trie and find_HGNC_symbols
#


def test_load_or_build_Trie_load_internal(tmp_path):
  # non-existing tree file and fake URL require it to solely rely on the internal file
  fakeFile = tmp_path / "testTree.txt"
  trie = load_or_build_Trie(fakeFile, FAKE_URL)
  matches = trie.search_in_text(TEST_TEXT)
  found = [m for _, m in matches]
  for gene in GENES:
    assert gene in found


def test_load_or_build_Trie_load_local(monkeypatch, tmp_path):
  # Test the case where internal resource fails, but local file exists.

  # First, force importlib.resources.files to raise an Exception.
  monkeypatch.setattr(
    "ohcrn_lei.extractHGNCSymbols.importlib.resources.files",
    lambda pkg: (_ for _ in ()).throw(Exception("Fake Exception")),
  )
  # Also provide a fake URL so re-building fails
  # Create a temporary file with a valid serialized Trie.
  trie = Trie()
  for gene in GENES:
    trie.insert(gene)
  serialized = trie.serialize()
  trie_file = tmp_path / "hgncTrie.txt"
  trie_file.write_text(serialized, encoding="utf-8")

  # test the actual method
  trie = load_or_build_Trie(str(trie_file), FAKE_URL)

  # validate that the resulting trie works
  text = "We found variants in MTHFR, CHEK2 and UBE2I."
  matches = trie.search_in_text(text)
  found = {word for (_, word) in matches}
  for gene in GENES:
    assert gene in found


def test_load_or_build_Trie_build_from_URL(monkeypatch, tmp_path):
  # Test the fallback: neither internal nor local file loaded, so build from URL.
  # Make internal resource fail.
  monkeypatch.setattr(
    "ohcrn_lei.extractHGNCSymbols.importlib.resources.files",
    lambda pkg: (_ for _ in ()).throw(Exception("Resource not found")),
  )
  # Use non-existing temporary file to fail local file test and later cache.
  trie_file = tmp_path / "hgncTrie.txt"

  def fake_get(*args, **kwargs):
    return FakeResponse(FAKE_TSV)

  monkeypatch.setattr("ohcrn_lei.extractHGNCSymbols.requests.get", fake_get)

  # test the actual method
  trie = load_or_build_Trie(str(trie_file), FAKE_URL)

  # validate
  matches = trie.search_in_text(TEST_TEXT)
  found = {word for (_, word) in matches}
  assert "NoMatch" not in found
  for gene in GENES:
    assert gene in found


def test_load_or_build_Trie_broken_internal_localIO(monkeypatch, tmp_path):
  # Test the case where internal resource is broken
  # and the local cache is unreadable.

  # First, force importlib.resources.files point to a
  # mock file containing a broken Trie serialization.
  broken_serialization = "[2"
  fake_internal_dir = tmp_path / "data"
  fake_internal_dir.mkdir()
  fake_internal_file = fake_internal_dir / "hgncTrie.txt"
  fake_internal_file.write_text(broken_serialization, encoding="utf-8")
  monkeypatch.setattr(
    "ohcrn_lei.extractHGNCSymbols.importlib.resources.files", lambda pkg: tmp_path
  )
  # Create a temporary file with a valid serialized Trie.
  trie = Trie()
  for gene in GENES:
    trie.insert(gene)
  serialized = trie.serialize()
  trie_file = tmp_path / "hgncTrie.txt"
  trie_file.write_text(serialized, encoding="utf-8")
  # cause an IO error by making the file unreadable
  trie_file.chmod(0o200)

  # test the actual method
  with pytest.raises(SystemExit):
    trie = load_or_build_Trie(str(trie_file), FAKE_URL)


def test_load_or_build_Trie_broken_local(monkeypatch, tmp_path):
  # Test the case where local cache file is broken.

  # First, force importlib.resources.files error out
  monkeypatch.setattr(
    "ohcrn_lei.extractHGNCSymbols.importlib.resources.files",
    lambda pkg: (_ for _ in ()).throw(Exception("test")),
  )
  # Create a temporary file with a broken serialized Trie.
  broken_serialization = "[2"
  trie_file = tmp_path / "hgncTrie.txt"
  trie_file.write_text(broken_serialization, encoding="utf-8")

  # test the actual method
  with pytest.raises(SystemExit):
    load_or_build_Trie(str(trie_file), FAKE_URL)


def test_find_HGNC_symbols(monkeypatch, tmp_path):
  # For find_HGNC_symbols, force load_or_build_Trie to use our FakeTrie with controlled content.
  trie = Trie()
  # Insert some gene symbols.
  for gene in GENES:
    trie.insert(gene)
  # Monkeypatch load_or_build_Trie (in our module) to return our fake_trie.
  monkeypatch.setattr(
    "ohcrn_lei.extractHGNCSymbols.load_or_build_Trie", lambda file, url: trie
  )
  # Also, patch parse_HGNC_from_URL in case it is called.
  monkeypatch.setattr(
    "ohcrn_lei.extractHGNCSymbols.parse_HGNC_from_URL", lambda url: trie
  )

  found = find_HGNC_symbols(TEST_TEXT)
  for gene in GENES:
    assert gene in found
