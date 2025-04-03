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

import json
import re
import sys
from typing import Any, List

"""
compare_json.py compares JSON files containing the extraction
results from OHCRN-LEI against a benchmark JSON file and counts
TPs, FPs and FNs, which are then output as a TSV table.

It is called by evaluation.sh

First argument is the reference JSON, second argument is the
JSON to be evaluated.
"""

args = sys.argv[1:]
refJSON = args[0]
testJSON = args[1]


def die(msg):
  print(msg, file=sys.stderr)
  sys.exit(1)


with open(refJSON, "r") as stream:
  refData = json.load(stream)

with open(testJSON, "r") as stream:
  testData = json.load(stream)


def forceList(x: Any) -> List[Any]:
  """
  Forces any given input to data type list.

  Args:
    any input

  Returns:
    A listified version of the input
  """
  if type(x) is not list:
    if type(x) is dict:
      return [v for v in x.values() if v is not None and v != ""]
    elif type(x) is set:
      return list(x)
    elif x is None or x == "":
      return []
    else:
      return [x]
  else:
    return x


def normalizeNames(xs: List[str]) -> List[str]:
  """
  Normalizes strings and identifiers to a common format to make
  them more comparable by removing prefixes and brackets and
  converting them to all upper-case.

  Args:
    A list of strings to be normalized

  Returns:
    The list of normalized strings
  """
  out: List[str] = []
  for x in xs:
    # normalize hgvs by removing prefixes and brackets
    x = re.sub(r"Chr.+:g\.", "", x)
    x = re.sub(r"^g\.|^c\.|^p\.", "", x)
    x = re.sub(r"^\(|\)$", "", x)
    if re.match(r"^\d+-\d+$", x):
      x = re.sub(r"-\d+$", "", x)
    # normalize omim, clinvar, dbsnp
    x = re.sub(r"^OMIM\D+", "", x)
    x = re.sub(r"^Clinvar[^V]*", "", x, flags=re.IGNORECASE)
    x = re.sub(r"^dbSNP[^r]*", "", x, flags=re.IGNORECASE)
    # normalize chromosomes
    if re.match(r"^ChrX$|^ChrY$|^Chr\d$", x, flags=re.IGNORECASE):
      x = re.sub(r"Chr", "", x, flags=re.IGNORECASE)
    # remove location tags
    x = re.sub(
      r" ?\(Toronto$| ?\(Kingston$| ?\(Ottawa| ?\(London| ?\(Orillia.*| ?\(Mississauga",
      "",
      x,
      flags=re.IGNORECASE,
    )
    # convert everything to uppercase for case insensitive matching
    x = x.upper()
    # treat NOT SPECIFIED or REDACTED as empty values
    if x not in ["NOT SPECIFIED", "REDACTED", "N/A"]:
      out.append(x)
  return out


def greedyPairOff(xs: List, ys: List) -> dict[str, Any]:
  """
  Calculates the number of matches between two lists and outputs it
  together with the unmatched items of each input list.

  Args:
    xs: A list of items
    ys: Another list of items

  Returns:
    A dictionary listing the number of hits, as well as lists of unpaired items from x and y.
  """
  taken_is = set()
  taken_js = set()
  for i in range(len(xs)):
    j = 0
    for j in range(len(ys)):
      if j not in taken_js and xs[i] == ys[j]:
        taken_is.add(i)
        taken_js.add(j)
        break
  unused_is = set(i for i in range(len(xs))) - taken_is
  unused_js = set(j for j in range(len(ys))) - taken_js
  unused_xs = [xs[i] for i in unused_is]
  unused_ys = [ys[j] for j in unused_js]
  return {"hits": len(taken_is), "unused_xs": unused_xs, "unused_ys": unused_ys}


def printTable(data: dict[str, dict[str, Any]]) -> None:
  """
  Pretty-prints a dict as a table.

  Args:
    data: the input dictionary to be printed
  """

  def list2str(x):
    if type(x) is list:
      return "|".join(x)
    else:
      return str(x)

  colnames = list(data.values())[0].keys()
  print("\t".join(colnames))
  for rowname, row_dict in data.items():
    valStr = [list2str(v) for v in row_dict.values()]
    print(rowname + "\t" + "\t".join(valStr))


output: dict[str, dict] = {}
for pageKey in refData:
  if pageKey not in testData:
    die("Missing page key!")
  for key, refval in refData[pageKey].items():
    if "explanation" in key:
      continue
    if key not in testData[pageKey]:
      die(f"missing key: {key}")
    testval = testData[pageKey][key]

    refval = normalizeNames(forceList(refval))
    testval = normalizeNames(forceList(testval))

    matches = greedyPairOff(refval, testval)
    tp = matches["hits"]
    fn = len(matches["unused_xs"])
    fp = len(matches["unused_ys"])
    # incorrect extractions show off as both fp and fn
    # e.g. extracting 'HE' instead of 'CHEK2'
    # so to prevent double-counting we only count them as fp
    fn = max(fn - fp, 0)
    # if there's nothing to extract from this report, then
    # nothing is the correct response
    if len(refval) == 0 and len(testval) == 0:
      tp = 1

    if key in output:
      output[key]["tp"] = output[key]["tp"] + tp
      output[key]["fn"] = output[key]["fn"] + fn
      output[key]["fp"] = output[key]["fp"] + fp
      output[key]["fn_list"].append(matches["unused_xs"])
      output[key]["fp_list"].append(matches["unused_ys"])
    else:
      output.update(
        {
          key: {
            "tp": tp,
            "fn": fn,
            "fp": fp,
            "fn_list": matches["unused_xs"],
            "fp_list": matches["unused_ys"],
          }
        }
      )

printTable(output)
