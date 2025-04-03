<h1 align="center">🌺🌺🌺🌺🌺🌺 OHCRN-LEI 🌺🌺🌺🌺🌺🌺</h1>
<p align="center">The Ontario Hereditary Cancer Research Network - LLM-based Extraction of Information
</p>

<p align="center">
<a href="#overview">Overview</a> • 
<a href="#getting-started">Getting started</a> • 
<a href="#contributing">Contributing</a> • 
<a href="#citation">Citation</a>
</p>

## Status
[![Python application](https://github.com/courtotlab/ohcrn_lei/actions/workflows/python-app.yml/badge.svg)](https://github.com/courtotlab/ohcrn_lei/actions/workflows/python-app.yml) 
![GitHub Release](https://img.shields.io/github/v/release/courtotlab/ohcrn_lei?include_prereleases)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

## Overview

The `ohcrn-lei` processes `PDF` or `TXT` files of clinical reports and extracts desired information from it, which will be output in `json` format. 

LEI currently supports the following built-in extraction tasks:
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

## Getting started
### Prerequisites ###
OHCRN-LEI requires `poppler` to be installed. If you don't have `poppler` installed already, you can do so as follows:

**MacOS (via homewbrew):**
```bash
$ brew install poppler
```
**Debian/Ubuntu:**
```bash
$ sudo apt install poppler-utils
```

We also recommend `uv` for a faster and easier installation process. (It only takes seconds!)

**MacOS (via homewbrew):**
```bash
$ brew install uv
```
**Linux:**
```bash
$ curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Installation ###
**Preliminarily:**
Install directly from github via `uv`:
```bash
$ uv tool install "ohcrn-lei @ git+https://github.com/courtotlab/ohcrn_lei"
```
<!-- 
**🚧🚧 After deployment on pypi becomes available: 🚧🚧**

With `uv` (fastest and easiest, if available):
```bash
uv tool install ohcrn_lei
```

With `pip` (slower):
```bash
# This will require python 3.13 or higher to be installed!
pipx install --user ohcrn_lei
``` -->

### Usage
After installation, you can run the `ohcrn-lei` in your command line. For example, to run the `report` extraction task on the file `example.pdf`, run:

```bash
ohrcn-lei --task report -outfile output.json example.pdf
```

Currently, the `report`, `molecular_test` and `variant` task are supported out-of-the-box. However, you can also [create your own custom tasks](#creating-custom-tasks). 

The full set of parameters can be found below:

```text
usage: ohcrn-lei [-h] [-b PAGE_BATCH] [-t TASK] [-o OUTFILE]
                 [--mock-LLM] [--no-ocr]
                 filename

Extract data from report file.

positional arguments:
  filename              Path to the report file to process.

options:
  -h, --help            show this help message and exit
  -b, --page-batch PAGE_BATCH
                        Number of pages to be processed at a given
                        time. Default=2
  -t, --task TASK       Specify the extraction task. This can either be
                        a pre-defined task
                        ('report','molecular_test','variant')or a plain
                        *.txt file with a task definition. See
                        documentationfor the task definition file
                        format specification.Default: report
  -o, --outfile OUTFILE
                        Output file or '-' for stdout (default)
  --mock-LLM            Don't make real LLM call, produce mock output
                        instead.
  --no-ocr              Disable OCR processing.
```

### Creating custom tasks

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

## Contributing
### Build process
To build the project from source, use [`uv`](https://docs.astral.sh/uv/#installation)
```bash
$ git clone https://github.com/courtotlab/ohcrn_lei.git
$ cd ohcrn_lei
$ uv build
```
The resulting `.whl` file will be n the `dist/` directory.

### Code quality
Unit tests are located in the `tests/` directory. To run them use 
```bash
$ uv run pytest
```

You can lint and format the code with `ruff`:
```bash
$ uv run ruff check
$ uv run ruff format
```

### Pull requests
If you are an outside contributor, you'll want to [fork the repo]((https://github.com/courtotlab/ohcrn_lei/fork)) first. Members of the Courtot Lab can create a branch on this repo instead.

1. Create your feature branch (`git checkout -b feature/fooBar`)
2. Commit your changes (`git commit -am 'Add some fooBar'`)
3. Push to the branch (`git push origin feature/fooBar`)
4. Test 
4. Open a [pull request](https://github.com/courtotlab/ohcrn_lei/compare).

## Authors
 * [Andres Melani de la Hoz](https://github.com/afmelani3365)
 * [Jochen Weile](https://github.com/jweile)

## Citation
Coming soon.