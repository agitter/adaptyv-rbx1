#!/usr/bin/env python3
"""
Convert a moPPIt results CSV to FASTA format.
Sequences are numbered 1-indexed with annotations seq1, seq2, etc.

Usage:
    python csv_to_fasta.py <input.csv> [output.fasta] [--top N]

Examples:
    python csv_to_fasta.py results_priority_affinity_filtered.csv
    python csv_to_fasta.py results_priority_affinity_filtered.csv candidates.fasta
    python csv_to_fasta.py results_priority_affinity_filtered.csv candidates.fasta --top 100
"""

import argparse
import csv

parser = argparse.ArgumentParser(description="Convert moPPIt results CSV to FASTA.")
parser.add_argument("input_file", help="Input CSV file")
parser.add_argument("output_file", nargs="?", default=None, help="Output FASTA file (default: stdout)")
parser.add_argument("--top", type=int, default=None, metavar="N", help="Only write the first N sequences")
args = parser.parse_args()

lines = []
with open(args.input_file, newline="") as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader, start=1):
        if args.top is not None and i > args.top:
            break
        lines.append(f">seq{i}")
        lines.append(row["Sequence"])

output = "\n".join(lines) + "\n"

if args.output_file:
    with open(args.output_file, "w") as f:
        f.write(output)
    print(f"Wrote {len(lines) // 2} sequences to {args.output_file}")
else:
    print(output, end="")
