"""Script pour executer l'approche classique de decouverte de PFDs.

Usage:
  python3 experiments/run_classical.py                          # tous les datasets
  python3 experiments/run_classical.py --dataset t1             # un seul dataset
  python3 experiments/run_classical.py --dataset t1 --min-support 10 --min-confidence 0.95
  python3 experiments/run_classical.py --dataset t1 --max-prefix-len 5
"""

import sys
import os
import argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.data_loader import load_csv, list_datasets
from src.classical_pipeline import run_classical_pipeline
from src.evaluation import compute_metrics, save_results


def main():
    parser = argparse.ArgumentParser(
        description="Approche classique de decouverte de PFDs (filtrable par dataset)"
    )
    parser.add_argument(
        "--dataset", type=str, default=None,
        help="Nom du dataset a traiter (ex: t1). Par defaut : tous les datasets.",
    )
    parser.add_argument(
        "--min-support", type=int, default=5,
        help="Support minimum pour garder une PFD (defaut : 5)",
    )
    parser.add_argument(
        "--min-confidence", type=float, default=0.85,
        help="Confidence minimum pour garder une PFD (defaut : 0.85)",
    )
    parser.add_argument(
        "--max-prefix-len", type=int, default=4,
        help="Longueur maximale des prefixes explores (defaut : 4)",
    )
    args = parser.parse_args()

    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    datasets = list_datasets(data_dir)

    all_results = []

    for folder, files in datasets.items():
        for filepath in files:
            dataset_name = os.path.basename(filepath).replace(".csv", "")

            # Filtrage par dataset (meme logique que run_agentic.py)
            if args.dataset and args.dataset not in dataset_name:
                continue

            print(f"\n{'='*80}")
            print(f"Dataset: {folder}/{dataset_name}")
            print(f"{'='*80}")

            df = load_csv(filepath)
            print(f"Shape: {df.shape}, Colonnes: {list(df.columns)}")

            results = run_classical_pipeline(
                df,
                min_support=args.min_support,
                min_confidence=args.min_confidence,
                max_prefix_len=args.max_prefix_len,
            )

            # Sauvegarder
            save_path = save_results(results, "classical", f"{folder}_{dataset_name}")
            print(f"Resultats sauvegardes: {save_path}")

            metrics = compute_metrics(results, f"classical/{folder}/{dataset_name}")
            all_results.append(metrics)

    if not all_results:
        suffix = f" pour '{args.dataset}'" if args.dataset else ""
        print(f"\nAucun dataset trouve{suffix}.")
        return

    # Resume
    print(f"\n\n{'='*80}")
    print("RESUME GLOBAL - Approche Classique")
    print(f"{'='*80}")
    print(f"{'Dataset':<40} {'PFDs':>6} {'Interessantes':>14} {'Conf.moy':>10} {'Temps(s)':>10}")
    print("-" * 85)
    for m in all_results:
        print(
            f"{m['approach']:<40} {m['num_pfds']:>6} {m['num_interesting']:>14} "
            f"{m['avg_confidence']:>10.4f} {m['execution_time']:>10.2f}"
        )


if __name__ == "__main__":
    main()
