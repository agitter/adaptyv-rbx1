#!/bin/bash
set -e

echo "Working directory: $(pwd)"
echo "GPU info:"
grep -i "GPUs_" $_CONDOR_MACHINE_AD

# Arguments passed from HTCondor submit file
JOB_ID=$1
LENGTH=$2
MOTIFS=$3
# Weights are passed as a single quoted string "w1 w2 w3 w4 w5 w6"
WEIGHTS=$4
N_BATCHES=$5

echo "job_id=$JOB_ID length=$LENGTH motifs=$MOTIFS weights=$WEIGHTS n_batches=$N_BATCHES"

OUTPUT_FILE="${_CONDOR_JOB_IWD}/samples_${JOB_ID}.csv"

# Target RBX-1 sequence from https://proteinbase.com/competitions/gem-adaptyv-rbx1
TARGET_PROTEIN="MAAAMDVDTPSGTNSGAGKKRFEVKKWNAVALWAWDIVVDNCAICRNHIMDLCIECQANQASATSEECTVAWGVCNHAFHFHCISRWLKTRQVCPLDNREWEFQKYGH"

cd /workspace/moPPIt

python -u /workspace/moPPIt/moppit.py \
    --output_file "$OUTPUT_FILE" \
    --length "$LENGTH" \
    --n_batches "$N_BATCHES" \
    --weights $WEIGHTS \
    --motifs "$MOTIFS" \
    --motif_penalty \
    --objectives Hemolysis Non-Fouling Half-Life Affinity Motif Specificity \
    --target_protein "$TARGET_PROTEIN"

gzip "$OUTPUT_FILE"
