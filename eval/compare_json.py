import json
import re
import sys

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


def forceList(x):
  """
  Forces any given input to data type list.
  """
  if type(x) is not list:
    if type(x) is dict:
      return [v for v in x.values() if v is not None and v != ""]
    elif type(x) is set:
      return list(set)
    elif x is None or x == "":
      return []
    else:
      return [x]
  else:
    return x


def normalizeNames(xs):
  """
  Normalizes strings and identifiers to a common format to make
  them more comparable by removing prefixes and brackets and
  converting them to all upper-case.
  """
  out = []
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


def greedyPairOff(xs, ys):
  """
  Calculates the number of matches between two lists and outputs it
  together with the unmatched items of each input list.
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


def printTable(data: dict) -> None:
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


output = {}
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
