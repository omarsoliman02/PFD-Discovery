"""Script pour executer l'approche classique sur tous les datasets."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.data_loader import load_csv, list_datasets
from src.classical_pipeline import run_classical_pipeline
from src.evaluation import compute_metrics, save_results

MIN_SUPPORT = 5
MIN_CONFIDENCE = 0.85
MAX_PREFIX_LEN = 4


def main():
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    datasets = list_datasets(data_dir)

    all_results = []

    for folder, files in datasets.items():
        for filepath in files:
            dataset_name = os.path.basename(filepath).replace(".csv", "")
            print(f"\n{'='*80}")
            print(f"Dataset: {folder}/{dataset_name}")
            print(f"{'='*80}")

            df = load_csv(filepath)
            print(f"Shape: {df.shape}, Colonnes: {list(df.columns)}")

            results = run_classical_pipeline(
                df,
                min_support=MIN_SUPPORT,
                min_confidence=MIN_CONFIDENCE,
                max_prefix_len=MAX_PREFIX_LEN,
            )

            # Sauvegarder
            save_path = save_results(results, "classical", f"{folder}_{dataset_name}")
            print(f"Resultats sauvegardes: {save_path}")

            metrics = compute_metrics(results, f"classical/{folder}/{dataset_name}")
            all_results.append(metrics)

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
