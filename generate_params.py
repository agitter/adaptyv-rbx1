#!/usr/bin/env python3
"""
Generate moppit_params.csv for HTCondor sweeps over moPPIt input parameters.

Usage:
    python generate_params.py

Edit the configuration sections below to expand or modify the parameter search space.
The output CSV has one row per job, with a unique job_id that matches the HTCondor
$(Process) index so outputs can be traced back to inputs.
"""

import csv
import itertools

# ---------------------------------------------------------------------------
# TARGET PROTEIN
# The protein sequence is fixed across all runs and embedded in moppit.sh,
# not in the params CSV. Edit moppit.sh if you change the target protein.
# Target protein length determines valid motif ranges below.
TARGET_LENGTH = 108  # length of the demo target protein

# ---------------------------------------------------------------------------
# PEPTIDE LENGTHS
# The authors use length 10 in all manuscript examples. Therapeutic peptides
# are typically 5-25 residues; shorter peptides are faster to generate and
# easier to synthesize but may lack affinity.
LENGTHS = [10, 15, 20, 25]

# ---------------------------------------------------------------------------
# MOTIFS
# Sliding windows across the full target protein since the epitope is unknown.
# Window sizes match the peptide lengths above — a motif wider than the peptide
# length makes little biological sense.
# Format: "start-end" (1-indexed, inclusive), matching moPPIt convention.
WINDOW_SIZE = 20   # residues per motif window
WINDOW_STEP = 10   # step between windows (50% overlap)

motifs = []
for start in range(1, TARGET_LENGTH - WINDOW_SIZE + 2, WINDOW_STEP):
    end = min(start + WINDOW_SIZE - 1, TARGET_LENGTH)
    motifs.append(f"{start}-{end}")

# ---------------------------------------------------------------------------
# OBJECTIVE WEIGHTS
# Order: Hemolysis Non-Fouling Half-Life Affinity Motif Specificity
# The authors' default is "1 1 1 4 4 2" — Affinity and Motif are prioritized.
# We sweep four strategies:
#   "balanced"        — default from manuscript
#   "affinity"        — prioritize binding affinity
#   "more-affinity"   — prioritize binding affinity more strongly
#   "max-affinity"    — maximize binding affinity above all else
#   "specificity"     — emphasize motif specificity for on-target selectivity
WEIGHT_SETS = {
    "balanced":        "1 1 1 4 4 2",
    "affinity":        "1 1 1 8 4 2",
    "more-affinity":   "1 1 1 8 2 1",
    "max-affinity":    "1 1 1 10 1 1",
    "specificity":     "1 1 1 4 8 4",
}

# ---------------------------------------------------------------------------
# NUMBER OF BATCHES
# The authors use 600 in manuscript examples (~14 hrs on a T4-class GPU).
# Use a smaller value for exploratory runs.
N_BATCHES = 600

# ---------------------------------------------------------------------------
# Generate all combinations
rows = []
job_id = 0
for length, motif, (weight_name, weights) in itertools.product(LENGTHS, motifs, WEIGHT_SETS.items()):
    rows.append({
        "job_id":      job_id,
        "length":      length,
        "motifs":      motif,
        "weights":     weights,
        "weight_name": weight_name,
        "n_batches":   N_BATCHES,
    })
    job_id += 1

output_file = "moppit_params.csv"
fieldnames = ["job_id", "length", "motifs", "weights", "weight_name", "n_batches"]

with open(output_file, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    f.write("# " + ",".join(fieldnames) + "\n")
    writer.writerows(rows)

print(f"Generated {len(rows)} jobs -> {output_file}")
print(f"  Lengths:      {LENGTHS}")
print(f"  Motifs:       {len(motifs)} windows of size {WINDOW_SIZE} with step {WINDOW_STEP}")
print(f"  Weight sets:  {list(WEIGHT_SETS.keys())}")
print(f"  n_batches:    {N_BATCHES}")
