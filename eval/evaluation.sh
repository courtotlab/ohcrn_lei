#!/usr/bin/env bash

set -euo pipefail +H

#directory containing OCR results for each document
OCR_DIR=input/ocr/
#directory containing manual (non-OCR) text conversions of each document
MANUAL_DIR=input/manual/
#directory where extraction outputs will be written
OUT_DIR=output/
#directory where manual reference extraction JSON are located
GS_DIR=reference/
#directory where TP/FP/FN evaluation metrics will be written
METRICS_DIR=metrics/
#directory where visualizations will be saved
VIS_DIR=vis/

#flag indicating whether to re-run the extraction if
# previous results already exist (i.e overwrite them)
RERUN_EXTRACTION=0

# if (( RERUN_EXTRACTION == 1 )); then
if [[ ! -e "${OUT_DIR}" || "${RERUN_EXTRACTION}" == 1 ]]; then

  # run extraction pipeline with OCR on all docs with all tasks
  for TASK in report molecular_test variant; do
    TARGET_DIR="${OUT_DIR}/ocr/${TASK}/"
    mkdir -p "${TARGET_DIR}"
    for DOC in "${OCR_DIR}"*.txt; do
      DOCNAME="$(basename "${DOC%.txt}")"
      ohcrn-lei -t "$TASK" \
        -o "${TARGET_DIR}${DOCNAME}.json" \
        --no-ocr "$DOC"
    done
  done

  #run extraction pipeline without OCR ("manual") on all docs with all tasks
  for TASK in report molecular_test variant; do
    TARGET_DIR="${OUT_DIR}/manual/${TASK}/"
    mkdir -p "${TARGET_DIR}"
    for DOC in "${MANUAL_DIR}"*.txt; do
      DOCNAME="$(basename "${DOC%.txt}")"
      ohcrn-lei -t "$TASK" \
        -o "${TARGET_DIR}${DOCNAME}.json" \
        --no-ocr "$DOC"
    done
  done

fi


# evaluate TP/FP/FN metrics on all results against reference
for METHOD in manual ocr; do
  for TASK in report molecular_test variant; do
    mkdir -p "${METRICS_DIR}${METHOD}/${TASK}/"
    for OUT_JSON in "${OUT_DIR}${METHOD}/${TASK}/"*json; do
      REFERENCE_JSON="${GS_DIR}${TASK}/$(basename ${OUT_JSON})"
      METRICS_FILE="${METRICS_DIR}${METHOD}/${TASK}/$(basename ${OUT_JSON%.json}).tsv"
      echo "Evaluating ${OUT_JSON}"
      python compare_json.py "${REFERENCE_JSON}" "${OUT_JSON}">"${METRICS_FILE}"
    done
    echo "Summarizing metrics for ${METHOD}/${TASK}"
    #sum over the metrics
    Rscript merge.R "${METRICS_DIR}${METHOD}/${TASK}/" "${METRICS_DIR}${METHOD}/${TASK}.tsv"
    #collect metrics in single file for each method/task combo
    tail -n +1 "${METRICS_DIR}${METHOD}/${TASK}/"*.tsv >"${METRICS_DIR}${METHOD}/${TASK}_collection.txt"
  done
done

# run visualization
echo "Visualization"
mkdir -p "${VIS_DIR}"
Rscript visualize.R "${METRICS_DIR}" "${VIS_DIR}"
