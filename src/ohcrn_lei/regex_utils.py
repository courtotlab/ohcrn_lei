import re

# from mavehgvs.patterns import protein as prot_regex
from enum import Enum
from typing import List


def get_coding_changes(text: str) -> List[str]:
  cDNA = Enum(
    "cDNA",
    [
      r"[cC]\.(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?(?:[GCTAgcta])?>(?:[GCTAgcta])",
      r"[cC]\.(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?(?:[GCTAgcta])?=",
      r"[cC]\.(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?(?:_(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?)?(?:[GCTAgcta]+)?delins(?:[GCTAgcta]+)",
      r"[cC]\.(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?(?:_(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?)?del(?:[GCTAgcta]+)?",
      r"[cC]\.(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?_(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?ins(?:[GCTAgcta]+)",
      r"[cC]\.(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?_(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?inv",
      r"[cC]\.(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?(?:_(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?)?dup(?:[GCTAgcta]+)?",
    ],
  )

  return get_matches(text, cDNA)


def get_genomic_changes(text: str) -> List[str]:
  gDNA = Enum(
    "gDNA",
    [
      r"g\.\d+(?:_\d+)?(?:[A-Za-z]*>[A-Za-z]*|(?:del|dup|ins|inv|delins)?[A-Za-z0-9]*)?"
    ],
  )
  return get_matches(text, gDNA)


def get_protein_changes(text: str) -> List[str]:
  # Replace the predefined aminoacid codes for a more general regex
  # that matches one capital letter followed by two lower ones
  # Protein patterns taken from https://github.com/VariantEffect/mavehgvs/blob/main/src/mavehgvs/patterns/protein.py
  # p_single_var = prot_regex.pro_single_variant.replace(prot_regex.amino_acid, "(?:[A-Z][a-z]{2})")
  # p_multi_var = prot_regex.pro_multi_variant.replace(prot_regex.amino_acid, "(?:[A-Z][a-z]{2})")
  protein_rgx = r"(?:[Pp]\.)?(?:[A-Z][a-zA-Z]{2}\d+(?:[A-Z][a-z]{2}|fs\*\d*|del|ins|dup|delins|Ter)+\d*)(?:;(?:[A-Z][a-z]{2}\d+(?:[A-Z][a-z]{2}|fs\*\d*|del|ins|dup|delins|Ter)\d*))*?"
  pDNA = Enum("pDNA", [protein_rgx])

  return get_matches(text, pDNA)


def get_matches(text: str, change_type: Enum) -> List[str]:
  # out = []
  # for regex in change_type:
  #   temp = re.findall(regex.name, text)
  #   out.extend(temp)

  out = [m for rgx in change_type for m in re.findall(rgx.name, text)]

  # remove duplicates
  out = list(set(out))

  return out


def get_variant_ids(text: str) -> List[str]:
  var_id_regex = [
    r"(?:OMIM)(?:\s*[:#])?\s*\d+",
    r"(?:Clinvar:)?([SRV]CV[A-Z0-9]{9})",
    r"(?:dbSNP:)?(rs\d+)",
    r"^COSMIC:COSM[0-9]+$",
    r"^clingene:CA\d+$",
    r"^uniprot:\.var:\d+$",
  ]

  found_ids = []

  for rgx in var_id_regex:
    found_ids.extend(re.findall(rgx, text))

  return list(set(found_ids))


def get_chromosomes(text: str) -> List[str]:
  chromosome_regex = r"^Chr([1-9]|1[0-9]|2[0-2]|X|Y)$"
  chrom_results = re.findall(chromosome_regex, text)

  return list(set(chrom_results))
