#!/bin/bash

#SBATCH --job-name=grounding_index_whole_table
#SBATCH --output=/home/pwiesenbach/CardioGuidelinesGraph/slurm/grounding_index_whole_table.log
#SBATCH --partition=long
#SBATCH --mem=16G

cd /home/pwiesenbach/CardioGuidelinesGraph

echo "==== GUIDELINE GROUNDING INDEX WHOLE TABLE START ===="

goal_title="2024 ESC Guidelines for the management of chronic coronary syndromes"
export BAML_LOG=OFF

docling_table_json_62="/prj/doctoral_letters/guide/data/guidelines/docling/pdf_pages/_62/tables/table_000.json"
docling_table_json_63="/prj/doctoral_letters/guide/data/guidelines/docling/pdf_pages/_63/tables/table_000.json"
docling_table_id="_62_63/table_000.json"
docling_footnotes_file="/tmp/docling_table_footnotes_${SLURM_JOB_ID:-$$}.txt"

if [[ -f "$docling_table_json_62" && -f "$docling_table_json_63" ]]; then
  echo "Docling table whole-table test: $docling_table_json_62"
  echo "Docling table whole-table test: $docling_table_json_63"
  cat > "$docling_footnotes_file" << 'EOF'
CABG, coronary artery bypass grafting; CAD, coronary artery disease; CCS, chronic coronary syndrome; FFR, fractional flow reserve; iFR, instantaneous wave-free ratio; IVUS, intravascular
ultrasound; LAD, left anterior descending; LV, left ventricular; LVEF, left ventricular ejection fraction; MVD, multivessel disease; OCT, optical coherence tomography; PCI, percutaneous
coronary intervention; QFR, quantitative flow ratio; STS, Society of Thoracic Surgeons; SYNTAX, SYNergy Between PCI with TAXUS and Cardiac Surgery.
a Class of recommendation.
b Level of evidence.

c Age, frailty, cognitive status, diabetes, and any other comorbidities.
d Multivessel disease with/out left main stem involvement, high anatomical complexity, and likelihood of revascularization completeness.
e Local expertise and outcomes, surgical and interventional risk.
EOF
  poetry run python /home/pwiesenbach/CardioGuidelinesGraph/src/cardio_graph/extraction_utils/entity_grounding_service_new.py \
    --docling-table-json "$docling_table_json_62" \
    --docling-table-json "$docling_table_json_63" \
    --docling-table-id "$docling_table_id" \
    --docling-footnotes-path "$docling_footnotes_file" \
    --docling-whole-table \
    --guideline-title "$goal_title" \
    --index-path "/prj/doctoral_letters/guide/data/grounding_index_docling_table_000_whole.json" \
    --rules-out-path "/prj/doctoral_letters/guide/data/extracted_rules_docling_table_000_whole.jsonl" \
    --model Qwen14b
  rm -f "$docling_footnotes_file"
  echo "==== GUIDELINE GROUNDING INDEX WHOLE TABLE END ===="
  exit 0
fi

echo "Docling table JSON files not found."
exit 1
