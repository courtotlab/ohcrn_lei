import io

import pytest
import requests

from ohcrn_lei.extractHGNCSymbols import (
  eliminate_submatches,
  filterAliases,
  load_or_build_Trie,
  parse_HGNC_from_URL,
)
from ohcrn_lei.trieSearch import Trie

# ----------------------------------------------------------------------
# Helpers / Mocks


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


# # Simulate a bad HTTP request by making raise_for_status() raise an exception.
# class BadResponse:
#     def __init__(self):
#         self.status_code = 404

#     def raise_for_status(self):
#         raise requests.exceptions.HTTPError("Not Found")

#     def iter_lines(self, decode_unicode=False):
#         return iter([])

#     def __enter__(self):
#         return self

#     def __exit__(self, *args):
#         pass
# ----------------------------------------------------------------------
# Tests for filterAliases


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
  # Prepare a fake TSV file stream. We include a header and two valid lines.
  fake_tsv = (
    "hgnc_id\tsymbol\tcol3\tcol4\tcol5\tcol6\tcol7\tcol8\taliases\tcol10\tlegacy\n"
    'HGNC:1\tGENE1\t-\t-\t-\t-\t-\t-\t"AL1|ab2|X1Y2"\t-\t"LEG1|lm3"\n'
    'HGNC:2\tGENE2\t-\t-\t-\t-\t-\t-\t"B2C|D3E"\t-\t\n'
  )

  # Create a fake response
  def fake_get(*args, **kwargs):
    return FakeResponse(fake_tsv)

  # monkeypatch.setattr(requests, "get", fake_get)
  monkeypatch.setattr("ohcrn_lei.extractHGNCSymbols.requests.get", fake_get)

  # Call the function. It will create a Trie and insert symbols.
  trie = parse_HGNC_from_URL("https://fake-url-for-test")
  # Check that the official symbols are inserted.
  # The official symbols are in column 2. Also aliases and legacy names are inserted if they pass the filter.
  # From first line: official: "GENE1"
  #   aliases: "AL1", "ab2", "X1Y2" -> apply filterAliases: "AL1" (has A1), "X1Y2" (has X1 or Y2) but "ab2" fails (no uppercase letter)
  #   legacy: "LEG1", "lm3" -> "LEG1" is valid, "lm3" is not.
  # From second line: official: "GENE2"; aliases: "B2C", "D3E" are valid if they match pattern:
  #   "B2C" : B2 is ok; "D3E": D3 is ok.
  #
  # Now verify (we assume Trie has a search or contains method).
  # For testing, we can re-serialize the trie and check whether the expected symbols exist by doing a search_in_text on a string that will match precisely them.
  test_text = " ".join(["GENE1", "AL1", "X1Y2", "LEG1", "GENE2", "B2C", "D3E"])
  matches = trie.search_in_text(test_text)
  found = {match for (_, match) in matches}
  expected = {"GENE1", "AL1", "X1Y2", "LEG1", "GENE2", "B2C", "D3E"}
  assert expected.issubset(found)


def test_parse_HGNC_from_URL_bad_response(monkeypatch):
  def fake_get(*args, **kwargs):
    return FakeResponse(None, status_code=404)

  monkeypatch.setattr("ohcrn_lei.extractHGNCSymbols.requests.get", fake_get)

  with pytest.raises(SystemExit):
    parse_HGNC_from_URL("https://fake-error-url")


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
# Since these functions interact with filesystem and package resources, we will simulate those.
#


# Fake Trie serialization/deserialization:
class FakeTrie(Trie):
  def __init__(self):
    super().__init__()
    self.words = set()

  def insert(self, word: str):
    self.words.add(word)

  def serialize(self):
    # We'll use a simple comma separated string
    return ",".join(sorted(self.words))

  @classmethod
  def deserialize(cls, data: str):
    trie = cls()
    if data.strip() == "":
      raise ValueError("Empty trie")
    for word in data.split(","):
      trie.insert(word)
    return trie

  # For search_in_text we implement a simple lookup:
  def search_in_text(self, text: str):
    matches = []
    # For each inserted word, if it occurs in text, record the first position.
    for word in self.words:
      pos = text.find(word)
      if pos >= 0:
        matches.append((pos, word))
    return matches


# Monkeypatch the Trie in our functions to use FakeTrie.
# @pytest.fixture(autouse=True)
# def patch_trie(monkeypatch):
#     monkeypatch.setattr("ohcrn_lei.trieSearch.Trie", FakeTrie)


def test_load_or_build_Trie_load_internal(monkeypatch, tmp_path):
  trieFile = tmp_path / "testTree.txt"
  trie = load_or_build_Trie(trieFile, "https://localhost/fakeURL")
  text = "We found variants in MTHFR, CHEK2 and UBE2I."
  matches = trie.search_in_text(text)
  matches_words = [m for _, m in matches]
  expected = ["MTHFR", "CHEK2", "UBE2I"]
  for ex in expected:
    assert ex in matches_words


# def test_load_or_build_Trie_load_local(monkeypatch, tmp_path):
#     # Test the case where internal resource fails, but local file exists.
#     # First, force importlib.resources.files to raise an Exception.
#     monkeypatch.setattr(
#         "ohcrn_lei.extractHGNCSymbols.importlib.resources.files",
#         lambda pkg: (_ for _ in ()).throw(Exception("Resource not found")),
#     )
#     # Create a temporary file with a valid serialized Trie.
#     fake_trie = FakeTrie()
#     fake_trie.insert("GENE_LOCAL")
#     serialized = fake_trie.serialize()
#     trie_file = tmp_path / "hgncTrie.txt"
#     trie_file.write_text(serialized, encoding="utf-8")
#     # Monkeypatch os.path.exists to return True when checking for the temporary file.
#     # monkeypatch.setattr(os, "path", SimpleNamespace(exists=lambda x: x == str(trie_file)))

#     # Patch open to use the temporary file.
#     original_open = open
#     def fake_open(filepath, mode="r", encoding=None):
#         if filepath == str(trie_file):
#             return original_open(filepath, mode, encoding=encoding)
#         else:
#             return original_open(filepath, mode, encoding=encoding)
#     monkeypatch.setattr("ohcrn_lei.extractHGNCSymbols.open", fake_open)

#     trie = load_or_build_Trie(str(trie_file), "https://fake-url")
#     matches = trie.search_in_text("GENE_LOCAL")
#     found = {word for (pos, word) in matches}
#     assert "GENE_LOCAL" in found

# def test_load_or_build_Trie_build_from_URL(monkeypatch, tmp_path):
#     # Test the fallback: neither internal nor local file loaded, so build from URL.
#     # Make internal resource fail.
#     monkeypatch.setattr(
#         "ohcrn_lei.extractHGNCSymbols.importlib.resources.files",
#         lambda pkg: (_ for _ in ()).throw(Exception("Resource not found")),
#     )
#     # Force os.path.exists to return False for the local file.
#     # monkeypatch.setattr(os, "path", SimpleNamespace(exists=lambda x: False))

#     # Prepare a fake TSV file as in earlier test.
#     fake_tsv = (
#         "hgnc_id\tsymbol\tcol3\tcol4\tcol5\tcol6\tcol7\tcol8\taliases\tcol10\tlegacy\n"
#         "HGNC:3\tGENE_URL\t-\t-\t-\t-\t-\t-\t\"AL3|NoMatch\"\t-\t\"LEG3\"\n"
#     )
#     def fake_get(*args, **kwargs):
#         return FakeResponse(fake_tsv)
#     monkeypatch.setattr(requests, "get", fake_get)

#     # Use a temporary file as cache.
#     trie_file = tmp_path / "hgncTrie.txt"
#     trie = load_or_build_Trie(str(trie_file), "https://fake-hgnc-url")
#     # Check that the newly built trie contains the official and valid alias/legacy symbols.
#     # Official: GENE_URL; aliases: "AL3" is valid; "NoMatch" likely fails if pattern not met (no uppercase letter followed by a digit? Actually, "N o" is not digit)
#     # legacy: "LEG3" is valid.
#     text = "GENE_URL AL3 LEG3"
#     matches = trie.search_in_text(text)
#     found = {word for (pos, word) in matches}
#     expected = {"GENE_URL", "AL3", "LEG3"}
#     assert expected.issubset(found)
#     # Also, check that the file was written (i.e. cache exists)
#     assert trie_file.read_text(encoding="utf-8").strip() != ""

# def test_find_HGNC_symbols(monkeypatch, tmp_path):
#     # For find_HGNC_symbols, force load_or_build_Trie to use our FakeTrie with controlled content.
#     fake_trie = FakeTrie()
#     # Insert some gene symbols.
#     fake_trie.insert("GENE_A")
#     fake_trie.insert("GENE_B")
#     # Monkeypatch load_or_build_Trie (in our module) to return our fake_trie.
#     monkeypatch.setattr("ohcrn_lei.extractHGNCSymbols.load_or_build_Trie", lambda file, url: fake_trie)
#     # Also, patch parse_HGNC_from_URL in case it is called.
#     monkeypatch.setattr("ohcrn_lei.extractHGNCSymbols.parse_HGNC_from_URL", lambda url: fake_trie)

#     text = "This text contains GENE_A, something else and GENE_B."
#     result = find_HGNC_symbols(text)
#     # Since our FakeTrie.search_in_text is simple, it will return matches if the gene symbol appears.
#     assert "GENE_A" in result
#     assert "GENE_B" in result
