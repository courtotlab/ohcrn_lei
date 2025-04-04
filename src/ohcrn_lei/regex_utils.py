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

import re
from typing import List


def get_coding_changes(text: str) -> List[str]:
  """Extract coding HGVS strings via regex

  Args:
    text: input text

  Returns:
    A list of HGVS strings found in the text.

  """
  cDNA = [
    r"[cC]\.(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?(?:[GCTAgcta])?>(?:[GCTAgcta])",
    r"[cC]\.(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?(?:[GCTAgcta])?=",
    r"[cC]\.(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?(?:_(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?)?(?:[GCTAgcta]+)?delins(?:[GCTAgcta]+)",
    r"[cC]\.(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?(?:_(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?)?del(?:[GCTAgcta]+)?",
    r"[cC]\.(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?_(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?ins(?:[GCTAgcta]+)",
    r"[cC]\.(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?_(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?inv",
    r"[cC]\.(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?(?:_(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?)?dup(?:[GCTAgcta]+)?",
  ]

  return get_matches(text, cDNA)


def get_genomic_changes(text: str) -> List[str]:
  """Extract genomic HGVS strings via regex

  Args:
    text: input text

  Returns:
    A list of HGVS strings found in the text.

  """
  gDNA = [
    r"g\.\d+(?:_\d+)?(?:[A-Za-z]*>[A-Za-z]*|(?:del|dup|ins|inv|delins)?[A-Za-z0-9]*)?"
  ]
  return get_matches(text, gDNA)


def get_protein_changes(text: str) -> List[str]:
  """Extract protein HGVS strings via regex

  Args:
    text: input text

  Returns:
    A list of HGVS strings found in the text.

  """
  # Replace the predefined aminoacid codes for a more general regex
  # that matches one capital letter followed by two lower ones
  # Protein patterns taken from https://github.com/VariantEffect/mavehgvs/blob/main/src/mavehgvs/patterns/protein.py
  # from mavehgvs.patterns import protein as prot_regex
  # p_single_var = prot_regex.pro_single_variant.replace(prot_regex.amino_acid, "(?:[A-Z][a-z]{2})")
  # p_multi_var = prot_regex.pro_multi_variant.replace(prot_regex.amino_acid, "(?:[A-Z][a-z]{2})")
  pDNA = [
    r"(?:[Pp]\.)?(?:[A-Z][a-zA-Z]{2}\d+(?:[A-Z][a-z]{2}|fs\*\d*|del|ins|dup|delins|Ter)+\d*)(?:;(?:[A-Z][a-z]{2}\d+(?:[A-Z][a-z]{2}|fs\*\d*|del|ins|dup|delins|Ter)\d*))*?"
  ]
  # FIXME: Eliminate sub-matches (see trie search)
  return get_matches(text, pDNA)


def get_matches(text: str, change_type: List[str]) -> List[str]:
  """Find matches in a text string given a list of regexes

  Args:
    text: Input text
    change_type: A list of regexes to extract

  Returns:
    A list of matches

  """
  out = [m for rgx in change_type for m in re.findall(rgx, text)]

  # remove duplicates
  out = list(set(out))

  return out


def get_variant_ids(text: str) -> List[str]:
  """Extract variant IDs strings via regex

  Args:
    text: input text

  Returns:
    A list of variant IDs found in the text.

  """
  var_id_regex = [
    r"(?:OMIM)(?:\s*[:#])?\s*\d+",
    r"(?:Clinvar:)?([SRV]CV[A-Z0-9]{9})",
    r"(?:dbSNP:)?(rs\d+)",
    r"COSMIC:COSM[0-9]+",
    r"clingene:CA\d+",
    r"uniprot:\.var:\d+",
  ]

  found_ids = []

  for rgx in var_id_regex:
    found_ids.extend(re.findall(rgx, text))

  return list(set(found_ids))


def get_chromosomes(text: str) -> List[str]:
  """Extract chromosome labels via regex

  Args:
    text: input text

  Returns:
    A list of chromosome labels found in the text.

  """
  chromosome_regex = r"^Chr([1-9]|1[0-9]|2[0-2]|X|Y)$"
  chrom_results = re.findall(chromosome_regex, text)

  return list(set(chrom_results))
