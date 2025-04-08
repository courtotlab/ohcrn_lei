# Evaluating `ohcrn-lei` extraction performance

This directory contains code to evaluate the performance of `ohcrn-lei` in terms of precision and recall of data extraction. The evaluation is performed across three different extraction tasks ("report", "molecular_test" and "variant") on a set of clinial reports that were converted to text files both manually and via OCR.

The extracted data in JSON format is compared to a set of reference "gold-standard" extractions that were created manually.

Please [contact us](https://oicr.on.ca/researchers/dr-melanie-courtot/) to get access to the test dataset.

## Running the evaluation scripts:
**Requirements:** In addition to `ohcrn-lei`'s requirements (uv and poppler), the evaluation also requires an installation of `R`.

Extract the test data into the `eval/` directory:
```bash
$ tar xzf test_data.tgz
```

The test data is structured as follows:
```text
input/
╰─▶ manual/
╰─▶ ocr/
reference/
╰─▶ molecular_test/
╰─▶ report/
╰─▶ variant/
```

To run the `evaluation.sh` script:
```bash
# Using uv to provide access to virtual environment
$ uv run bash evaluation.sh
```

## What do the scripts do?
  * `evaluation.sh`: This script orchestrates the evaluation. It first runs `ohcrn-lei` on all the input texts.Then uses `compare_json.py` to compare the outputs to the gold standard reference and identify correct and incorrect extractions. It calls `merge.R` on these counts to generate overview tables, before finally calling `visualize.R` to generate plots illustrating the precision/recall performance.
  * `compare_json.py`: Compares the outputs of `ohcrn-lei` to a gold-standard reference JSON file and counts true-positives, false-positives and false-negatives.
  * `merge.R` collates the results of all the error counts for a given extraction task for manual or OCR documents.
  * `visualize.R`: Calculates precision and recall metrics and draws plots.

## Results:
The evaluation script will create the following directories:
  1. `output/` contains the JSON outputs produced by `ohcrn-lei` for each task on the manual and OCR text files.
  2. `metrics/` contains the true-positive, false-positive and false-negative counts, both for individual results as well as collated accross categories.
  3. `vis/` contrains the generated plots as `.pdf` files.

