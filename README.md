# 🌺🌺🌺🌺🌺🌺 OHCRN-LEI 🌺🌺🌺🌺🌺🌺 
The Ontario Hereditary Cancer Research Network - LLM-based Extraction of Information

[![Python application](https://github.com/courtotlab/ohcrn_lei/actions/workflows/python-app.yml/badge.svg)](https://github.com/courtotlab/ohcrn_lei/actions/workflows/python-app.yml)

## Table of contents
 1. [Overview](#overview)
 2. [Installation](#installation)
 3. [Using OHCRN-LEI](#usage)
 4. [Building OHCRN-LEI](#how-to-build-the-project)
 5. [Creating custom extraction tasks](#task-definition-format)

## Overview

The `ohcrn-lei` tool takes a `PDF` or `TXT` file of a clinical report and extracts desired information from it, which will be output in `json` format. 

It currently supports the following built-in extraction tasks:
  * **Report**: Extracts the following data:
    1. "report_date" (Collected On, Received On, etc in "YYYY-MM-DD" format).
    2. "report_type": Type of report.
    3. "testing_context": Purpose of the testing (clinical or research).
    4. "ordering_clinic": Name of the lab that ordered the test. 
    5. "testing/laboratory": Name of the lab that conducted the test.
  * **Molecular test**: 
    1. Sequencing Scope: Gene panel, Targeted variant testing, Whole exome sequencing (WES), Whole genome sequencing (WGS), Whole transcriptome sequencing (WTS).
    2. Tested Genes
    3. Sample Type: Amplified DNA, ctDNA, Other DNA enrichments, Other RNA fractions, polyA+ RNA, Ribo-Zero RNA, Total DNA, Total RNA.
    4. Analysis Type: Variant analysis, Microarray, Repeat expansion analysis, Karyotyping, Fusion analysis, Methylation analysis.
  * **Variants**:
    1. Variant Identifiers: e.g OMIM, Clinvar, dbSNP, etc
    2. Gene Symbol
    3. Transcript ID: NCBI or LRG.
    4. Variant descriptor in genomic context (gHGVS):
    5. Variant descriptor in coding sequence context (cHGVS)
    6. Amino Acid Change (pHGVS)
    7. Chromosome: The chromosome identifier.
    8. Exon: The exon number
    9. Reference genome build: ("GRCh37","GRCh38")

In addition to the built-in extraction tasks, additional tasks can also be provided via a task definition file (via the `-t` option). See [below](#task-definition-format) for the task definition file format requirements.

## Installation
### OS dependencies ###
OHCRN-LEI requires `poppler` to be installed. If you don't have `poppler` installed already, you can do so as follows:

**MacOS:**
```bash
$ brew install poppler
```
**Debian/Ubuntu:**
```bash
$ sudo apt install poppler-utils
```

### Preliminarily: ###
We recommend installing `ohcrn-lei` via `uv`. If you don't have `uv`, you can install it from [here](https://docs.astral.sh/uv/#installation). (It only takes seconds!)

  1. Download the wheel (`.whl`) file from the [latest release](https://github.com/courtotlab/ohcrn_lei/releases)
  2. Install the wheel file via `uv`.

```bash
# substitute the link below with the latest release
$ wget 'https://github.com/courtotlab/ohcrn_lei/releases/download/v0.2.0/ohcrn_lei-0.1.0-py3-none-any.whl'
$ uv tool install ohcrn_lei-0.1.0-py3-none-any.whl
```
### 🚧🚧 After deployment on pypi becomes available: 🚧🚧

With `uv` (fastest and easierst, if available):
```bash
uv tool install ohcrn_lei
```

With `pip` (slower):
```bash
# This will require python 3.13 or higher to be installed
pipx install --user ohcrn_lei
```

## Usage
After installation, you can run the `ohcrn-lei` in your command line.

For example, to run the `Report` extraction task on the file `example.pdf`, run:

```bash
ohrcn-lei --task report -outfile output.json example.pdf
```

The full set of parameters can be found below:

```text
usage: ohcrn-lei [-h] [--no-ocr] [-t TASK] [-o OUTFILE] filename

Extract data from report file.

positional arguments:
  filename              Path to the report file to process.

options:
  -h, --help            show this help message and exit
  --no-ocr              Disable OCR processing.
  -t, --task TASK       Specify the extraction task. This can either be a pre-
                        defined task ('report','molecular_test','variant')or a
                        plain *.txt file with a task definition. See
                        documentationfor the task definition file format
                        specification.Default: report
  -o, --outfile OUTFILE
                        Output file or '-' for stdout (default)
```

## How to build the project
To build the project, we recommend using [`uv`](https://docs.astral.sh/uv/#installation)
```bash
$ git clone https://github.com/courtotlab/ohcrn_lei.git
$ cd ohcrn_lei
$ uv build
```
## Task definition format

To create a new extraction task from scratch, you can create a new task definition file. The task definition file follows the following format

```text
##### START PROMPT #####
Enter your LLM prompt here. Must instruct the LLM to generate a JSON dictionary output.
##### END PROMPT #####
##### START PLUGINS #####
json_key=plugin_name
...
##### END PLUGINS #####
```

The following plugins are supported:
  * **trie_hgnc** : Extracts HGNC gene symbols and aliases using a Trie search algorithm.
  * **regex_hgvsg** : Extracts genomic HGVS strings using a regular expression search.
  * **regex_hgvsc** : Extracts coding sequence HGVS strings using a regular expression search.
  * **regex_hgvsp** : Extracts protein-level HGVS strings using a regular expression search.
  * **regex_variants** : Extracts variant IDs (OMIM,dbSNP,etc.) using a regular expression search.
  * **regex_chromosome** : Extracts chromosome identifiers using a regular expression search.

## Citation
Coming soon.