# 🌺🌺🌺🌺🌺🌺 OHCRN-LEI 🌺🌺🌺🌺🌺🌺 
The Ontario Hereditary Cancer Research Network - LLM-based Extraction of Information

The `ohcrn-lei` tool takes a `PDF` or `TXT` file of a clinical report and extracts desired information from it, which will be output in `json` format. 

It currently supports the following extraction tasks:
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


## Installation
### Preliminarily: ###
Until the project is deployed to pypi, it's better to check out the tool and run it without installing, via [`uv`](https://docs.astral.sh/uv/#installation):
```bash
$ git clone https://github.com/courtotlab/ohcrn_lei.git
$ cd ohcrn_lei
$ uv run ohcrn-lei
```
### 🚧🚧 After deployment on pypi becomes avaialble: 🚧🚧

With `uv` (fastest, if available):
```bash
uv tool install ohcrn_lei
```

With pip (slower):
```bash
pip install --user ohcrn_lei
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
