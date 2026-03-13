#!/usr/bin/env python3
"""
Merge all moPPIt output CSVs with their generating parameters and prioritize
candidate peptides using three scoring strategies.

Usage:
    python analyze_results.py

Inputs:
    output/samples_*.csv.gz       - moPPIt output files
    moppit_params.csv             - parameter file linking job_id to run parameters
    UniProt-aa-composition.txt    - UniProt amino acid frequency table

Outputs:
    results_merged.csv                        - all peptides with parameters, unsorted
    results_priority_affinity.csv             - ranked by Affinity only (all)
    results_priority_affinity_filtered.csv    - ranked by Affinity only (filtered)
    results_priority_motif.csv                - ranked by Affinity + Motif (all)
    results_priority_motif_filtered.csv       - ranked by Affinity + Motif (filtered)
    results_priority_balanced.csv             - ranked by Affinity + Motif + Specificity (all)
    results_priority_balanced_filtered.csv    - ranked by Affinity + Motif + Specificity (filtered)
    pairplot.png                              - seaborn pairplot of all 6 raw scores
"""

import re
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# ---------------------------------------------------------------------------
# Load UniProt amino acid frequencies from file
# Only the 20 standard amino acids (single letter codes A-Y) are used.
# Non-standard codes (X, B, U, Z, O) are excluded.
# ---------------------------------------------------------------------------
UNIPROT_FILE = Path("UniProt-aa-composition.txt")

uniprot_raw = pd.read_csv(UNIPROT_FILE, sep="\t")
uniprot_raw.columns = uniprot_raw.columns.str.strip()

# Keep only standard 20 amino acids (single uppercase letter, no X/B/U/Z/O)
standard_aa = set("ACDEFGHIKLMNPQRSTVWY")
uniprot_raw = uniprot_raw[uniprot_raw["1-letter code"].isin(standard_aa)]

# Parse percent string "9.76%" -> 0.0976
uniprot_raw["freq"] = uniprot_raw["Percent"].str.replace("%", "").astype(float) / 100.0

# Renormalize to sum to 1.0 over the 20 standard AAs
uniprot_raw["freq"] = uniprot_raw["freq"] / uniprot_raw["freq"].sum()

UNIPROT_FREQ = dict(zip(uniprot_raw["1-letter code"], uniprot_raw["freq"]))
print("Loaded UniProt AA frequencies:")
for aa, freq in sorted(UNIPROT_FREQ.items(), key=lambda x: -x[1]):
    print(f"  {aa}: {freq:.4f}")

# ---------------------------------------------------------------------------
# Score filters
# Affinity and Motif: target the upper modes visible in the pairplot
# Specificity and Half-Life: loose thresholds to only eliminate worst peptides
# ---------------------------------------------------------------------------
MIN_AFFINITY    = 8.0    # upper mode of bimodal Affinity distribution
MIN_MOTIF       = 0.5    # focus on the right mode
MIN_SPECIFICITY = 0.80   # loose lower tail cutoff (mean=0.916, std=0.063)
MIN_HALF_LIFE   = 25.0   # excludes lower peak

# ---------------------------------------------------------------------------
# Sequence filters
# ---------------------------------------------------------------------------
MAX_AA_FREQ_MULTIPLIER = 4.0  # observed freq must not exceed this multiple of UniProt background
MAX_CONSECUTIVE    = 3      # no run of identical AAs longer than this


def all_standard_aa(seq: str) -> bool:
    """Sequence contains only the 20 standard amino acids."""
    return all(aa in standard_aa for aa in seq)


def aa_frequency_ok(seq: str) -> bool:
    """No AA appears more than MAX_AA_FREQ_MULTIPLIER times its UniProt background frequency.
    e.g. W (UniProt 1.3%) may appear at most 5.2% of residues
    """
    n = len(seq)
    for aa in set(seq):
        observed = seq.count(aa) / n
        background = UNIPROT_FREQ.get(aa, 1.0)
        if observed > MAX_AA_FREQ_MULTIPLIER * background:
            return False
    return True


def no_consecutive_repeats(seq: str) -> bool:
    """No run of identical amino acids longer than MAX_CONSECUTIVE."""
    return not bool(re.search(r"(.)\1{" + str(MAX_CONSECUTIVE) + r",}", seq))


def sequence_filter_pass(seq: str) -> bool:
    return all_standard_aa(seq) and aa_frequency_ok(seq) and no_consecutive_repeats(seq)


def apply_all_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Apply score and sequence filters, printing a breakdown of removals."""
    n_start = len(df)

    # Score filters
    score_mask = (
        (df["Affinity"]    >= MIN_AFFINITY) &
        (df["Motif"]       >= MIN_MOTIF) &
        (df["Specificity"] >= MIN_SPECIFICITY) &
        (df["Half-Life"]   >  MIN_HALF_LIFE)
    )
    df_score = df[score_mask]
    print(f"  Score filters: {len(df_score)} remain ({n_start - len(df_score)} removed)")
    print(f"    Affinity < {MIN_AFFINITY}:         {(df['Affinity'] < MIN_AFFINITY).sum()}")
    print(f"    Motif < {MIN_MOTIF}:             {(df['Motif'] < MIN_MOTIF).sum()}")
    print(f"    Specificity < {MIN_SPECIFICITY}:    {(df['Specificity'] < MIN_SPECIFICITY).sum()}")
    print(f"    Half-Life <= {MIN_HALF_LIFE}:       {(df['Half-Life'] <= MIN_HALF_LIFE).sum()}")

    # Sequence filters
    seq_mask = df_score["Sequence"].apply(sequence_filter_pass)
    df_filtered = df_score[seq_mask]
    n_seq_removed = len(df_score) - len(df_filtered)
    print(f"  Sequence filters: {len(df_filtered)} remain ({n_seq_removed} removed)")
    print(f"    Non-standard AA:     {(~df_score['Sequence'].apply(all_standard_aa)).sum()}")
    print(f"    AA freq > {MAX_AA_FREQ_MULTIPLIER}x UniProt: {(~df_score['Sequence'].apply(aa_frequency_ok)).sum()}")
    print(f"    Consecutive repeats: {(~df_score['Sequence'].apply(no_consecutive_repeats)).sum()}")

    return df_filtered


# ---------------------------------------------------------------------------
# Load and merge all output files with parameters
# ---------------------------------------------------------------------------
OUTPUT_DIR  = Path("output")
PARAMS_FILE = Path("moppit_params.csv")

params = pd.read_csv(
    PARAMS_FILE,
    comment="#",
    header=None,
    names=["job_id", "length", "motifs", "weights", "weight_name", "n_batches"],
)

records = []
missing = []
for job_id in params["job_id"]:
    path = OUTPUT_DIR / f"samples_{job_id}.csv.gz"
    if not path.exists():
        missing.append(job_id)
        continue
    df = pd.read_csv(
        path,
        header=0,
        names=["Sequence", "Hemolysis", "Non-Fouling", "Half-Life",
               "Affinity", "Motif", "Specificity"],
    )
    df["job_id"] = job_id
    records.append(df)

if missing:
    print(f"\nWarning: {len(missing)} output files not found for job_ids: {missing}")

all_peptides = pd.concat(records, ignore_index=True)
merged = all_peptides.merge(params, on="job_id", how="left")

print(f"\nMerged {len(merged)} peptides from {len(records)} jobs")

# ---------------------------------------------------------------------------
# Pairplot of all 6 raw scores
# ---------------------------------------------------------------------------
SCORE_COLS = ["Hemolysis", "Non-Fouling", "Half-Life", "Affinity", "Motif", "Specificity"]

print("\nGenerating pairplot...")
g = sns.pairplot(
    merged[SCORE_COLS],
    plot_kws={"alpha": 0.3, "s": 5, "rasterized": True},
    diag_kind="kde",
)
g.figure.suptitle("moPPIt output scores — all peptides (raw)", y=1.02)
g.figure.savefig("pairplot.png", dpi=150, bbox_inches="tight")
plt.close()
print("Pairplot saved -> pairplot.png")

# ---------------------------------------------------------------------------
# Deduplication: keep the highest Affinity instance of each unique sequence
# ---------------------------------------------------------------------------
deduped = merged.sort_values("Affinity", ascending=False).drop_duplicates(
    subset="Sequence", keep="first"
).copy()
print(f"\nAfter deduplication: {len(deduped)} unique sequences "
      f"({len(merged) - len(deduped)} duplicates removed)")

# ---------------------------------------------------------------------------
# Compute composite scores on deduplicated set (before any filtering)
# Affinity is rescaled to [0,1] to be comparable with [0,1] scores
# ---------------------------------------------------------------------------
affinity_scaled = (deduped["Affinity"] - deduped["Affinity"].min()) / (
    deduped["Affinity"].max() - deduped["Affinity"].min()
)
deduped["score_affinity_motif"] = 0.5 * affinity_scaled + 0.5 * deduped["Motif"]

W_AFFINITY    = 0.4
W_MOTIF       = 0.4
W_SPECIFICITY = 0.2
deduped["score_balanced"] = (
    W_AFFINITY    * affinity_scaled +
    W_MOTIF       * deduped["Motif"] +
    W_SPECIFICITY * deduped["Specificity"]
)

# ---------------------------------------------------------------------------
# Priority 1: Affinity only
# ---------------------------------------------------------------------------
priority_affinity = deduped.sort_values("Affinity", ascending=False)
priority_affinity.to_csv("results_priority_affinity.csv.gz", index=False, compression="gzip")
print(f"\nPriority 1 (Affinity only) -> results_priority_affinity.csv ({len(priority_affinity)} rows)")

print("  Applying filters...")
filtered_affinity = apply_all_filters(priority_affinity)
filtered_affinity = filtered_affinity.sort_values("Affinity", ascending=False)
filtered_affinity.to_csv("results_priority_affinity_filtered.csv", index=False)
print(f"  Filtered -> results_priority_affinity_filtered.csv ({len(filtered_affinity)} rows)")

# ---------------------------------------------------------------------------
# Priority 2: Affinity + Motif
# ---------------------------------------------------------------------------
priority_motif = deduped.sort_values("score_affinity_motif", ascending=False)
priority_motif.to_csv("results_priority_motif.csv.gz", index=False, compression="gzip")
print(f"\nPriority 2 (Affinity + Motif) -> results_priority_motif.csv ({len(priority_motif)} rows)")

print("  Applying filters...")
filtered_motif = apply_all_filters(priority_motif)
filtered_motif = filtered_motif.sort_values("score_affinity_motif", ascending=False)
filtered_motif.to_csv("results_priority_motif_filtered.csv", index=False)
print(f"  Filtered -> results_priority_motif_filtered.csv ({len(filtered_motif)} rows)")

# ---------------------------------------------------------------------------
# Priority 3: Affinity + Motif + Specificity
# ---------------------------------------------------------------------------
priority_balanced = deduped.sort_values("score_balanced", ascending=False)
priority_balanced.to_csv("results_priority_balanced.csv.gz", index=False, compression="gzip")
print(f"\nPriority 3 (Affinity + Motif + Specificity) -> results_priority_balanced.csv ({len(priority_balanced)} rows)")

print("  Applying filters...")
filtered_balanced = apply_all_filters(priority_balanced)
filtered_balanced = filtered_balanced.sort_values("score_balanced", ascending=False)
filtered_balanced.to_csv("results_priority_balanced_filtered.csv", index=False)
print(f"  Filtered -> results_priority_balanced_filtered.csv ({len(filtered_balanced)} rows)")

# ---------------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------------
print("\nScore summary (deduplicated peptides, before filtering):")
print(deduped[["Affinity", "Motif", "Specificity", "Half-Life",
               "score_affinity_motif", "score_balanced"]].describe().round(3))
