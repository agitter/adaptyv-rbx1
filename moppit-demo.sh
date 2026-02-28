#!/bin/bash
set -e

# Prevent KeyError: 'getpwuid(): uid not found: 21155'
export TORCHINDUCTOR_CACHE_DIR=/tmp/torchinductor

echo "Working directory: $(pwd)"
echo "GPU info:"
grep -i "GPUs_" $_CONDOR_MACHINE_AD

python -u /workspace/moPPIt/moppit.py \
    --output_file './moppit-demo-samples.csv' \
    --length 10 \
    --n_batches 5 \
    --weights 1 1 1 4 4 2 \
    --motifs '16-31,62-79' \
    --motif_penalty \
    --objectives Hemolysis Non-Fouling Half-Life Affinity Motif Specificity \
    --target_protein MHVPSGAQLGLRPDLLARRRLKRCPSRWLCLSAAWSFVQVFSEPDGFTVIFSGLGNNAGGTMHWNDTRPAHFRILKVVLREAVAECLMDSYSLDVHGGRRTAAG
