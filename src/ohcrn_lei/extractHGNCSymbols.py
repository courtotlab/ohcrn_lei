from typing import List
import requests
import os
import re
from ohcrn_lei.trieSearch import Trie


def filterAliases(symbols: List[str]) -> List[str]:
  """
  Only allow aliases that have at least one uppercase character followed by a number and a length of at least 3
  """
  return [s for s in symbols if len(s) > 2 and re.search(r"[A-Z][0-9]", s)]


def parse_HGNC_from_URL(hgnc_url: str) -> Trie:
  """
  Read HGNC definitions file, pull all gene symbols from it
  and feed them into a search Trie.
  """
  # Create an empty trie
  trie = Trie()
  try:
    with requests.get(hgnc_url, stream=True) as response:
      response.raise_for_status()
      # Process the file line by line.
      for line in response.iter_lines(decode_unicode=True):
        if line and not line.startswith("hgnc_id"):  # Skip header and any empty lines.
          parts = line.split("\t")
          if len(parts) >= 11:
            # official HGNC gene symbol
            symbol = parts[1]
            trie.insert(symbol)
            # alternative "alias" gene names
            aliases = parts[8]
            if aliases:
              aliases = aliases.strip('"').split("|")
              for alias in filterAliases(aliases):
                trie.insert(alias)
            # outdated legacy gene names
            legacySymbols = parts[10]
            if legacySymbols:
              legacySymbols = legacySymbols.strip('"').split("|")
              for lsym in filterAliases(legacySymbols):
                trie.insert(lsym)
          else:
            print("Warning: No gene symbol in line ", line)
  except requests.exceptions.RequestException as e:
    print("Failed to download the HGNC file:", e)
  return trie


def load_or_build_Trie(trieFile: str, hgnc_url: str) -> Trie:
  """
  Trie to load a serialized search Trie for HGNC gene symbols from a given cache file.
  If it doesn't exist, build a new Trie from the HGNC source on the internet,
  serialize it and store it in the cache file.
  """
  if os.path.exists(trieFile):
    try:
      with open(trieFile, "r", encoding="utf-8") as infile:
        serialized = infile.read()
        trie = Trie.deserialize(serialized)
        print("Gene symbol Trie read from file.")
    except Exception as e:
      print(f"Error while reading file {e}")
    except ValueError as e:
      print(f"Format error while reading file: {e}")
  else:
    trie = parse_HGNC_from_URL(hgnc_url)
    print("Parsed gene symbols from HGNC into Trie.")
    serialized = trie.serialize()
    try:
      with open(trieFile, "w", encoding="utf-8") as file:
        file.write(serialized)
      print("Serialized gene symbol Trie saved.")
    except Exception as e:
      print(f"Error while writing file: {e}")

  return trie


def eliminate_submatches(matches: dict[int, str]) -> dict[int, str]:
  """
  Find all the submatches in the list of matches and remove them.
  E.g. "The gene is CHEK2." matches both "CHEK2" and "HE", but "HE" is
  a submatch of CHEK2 and would thus be discarded.
  """
  submatches = set()
  for i in range(len(matches)):
    (start_i, match_i) = matches[i]
    end_i = start_i - 1 + len(match_i)
    for j in range(len(matches)):
      if i == j:
        continue
      (start_j, match_j) = matches[j]
      end_j = start_j - 1 + len(match_j)
      if start_i >= start_j and end_i <= end_j:
        # then i is submatch of j
        submatches.add(i)
  cleanMatches = [matches[i] for i in range(len(matches)) if i not in submatches]
  return cleanMatches


def find_HGNC_symbols(text: str) -> List[str]:
  """
  Finds all HGNC gene symbols in a given piece of text
  """
  # Load Trie of HGNC symbols
  hgnc_url = "https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/non_alt_loci_set.txt"
  trie = load_or_build_Trie("hgncTrie.txt", hgnc_url)

  # Searching the text using the trie
  found_matches = trie.search_in_text(text)
  # Clean up results by removing submatches
  cleanMatches = eliminate_submatches(found_matches)

  # return(cleanMatches)
  out = [symbol for (idx, symbol) in cleanMatches]
  return out
