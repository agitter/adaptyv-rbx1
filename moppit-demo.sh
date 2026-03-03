#!/bin/bash
set -e

echo "GPU info:"
grep -i "GPUs_" $_CONDOR_MACHINE_AD

cd /workspace/moPPIt

python -u /workspace/moPPIt/moppit.py \
    --output_file "${_CONDOR_JOB_IWD}/moppit-demo-samples.csv" \
    --length 10 \
    --n_batches 5 \
    --weights 1 1 1 4 4 2 \
    --motifs '16-31,62-79' \
    --motif_penalty \
    --objectives Hemolysis Non-Fouling Half-Life Affinity Motif Specificity \
    --target_protein MHVPSGAQLGLRPDLLARRRLKRCPSRWLCLSAAWSFVQVFSEPDGFTVIFSGLGNNAGGTMHWNDTRPAHFRILKVVLREAVAECLMDSYSLDVHGGRRTAAG
