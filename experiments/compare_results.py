"""Script de comparaison entre approche classique et agentique sur un dataset.

Usage:
  python compare_results.py --dataset t1
  python compare_results.py --dataset t2 --llm gemini

Prerequis:
  export GOOGLE_API_KEY="AI..."
  export COHERE_API_KEY="..."
"""

import sys
import os
import argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.data_loader import load_csv, list_datasets
from src.classical_pipeline import run_classical_pipeline
from src.agentic_workflow import workflow1_feature_enriched, workflow2_guided_search
from src.evaluation import compare_approaches, save_results

MIN_SUPPORT = 5
MIN_CONFIDENCE = 0.85


def find_dataset(data_dir: str, name: str) -> str | None:
    """Trouve le chemin d'un dataset par son nom."""
    datasets = list_datasets(data_dir)
    for folder, files in datasets.items():
        for fp in files:
            if name in os.path.basename(fp):
                return fp
    return None


def main():
    parser = argparse.ArgumentParser(description="Comparer classique vs agentique")
    parser.add_argument("--dataset", required=True, help="Nom du dataset (ex: t1)")
    parser.add_argument("--llm", choices=["gemini", "cohere", "all"], default="all")
    args = parser.parse_args()

    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    filepath = find_dataset(data_dir, args.dataset)
    if not filepath:
        print(f"Dataset '{args.dataset}' non trouve")
        sys.exit(1)

    dataset_name = os.path.basename(filepath).replace(".csv", "")
    df = load_csv(filepath)
    print(f"Dataset: {dataset_name} ({df.shape[0]} lignes, {df.shape[1]} colonnes)")
    print(f"Colonnes: {list(df.columns)}\n")

    all_results = []

    # 1. Approche classique
    print(f"{'='*80}")
    print("APPROCHE CLASSIQUE")
    print(f"{'='*80}")
    classical = run_classical_pipeline(
        df, min_support=MIN_SUPPORT, min_confidence=MIN_CONFIDENCE
    )
    save_results(classical, "classical", dataset_name)
    all_results.append(("Classique", classical))

    # 2. Workflows agentiques
    llms = ["gemini", "cohere"] if args.llm == "all" else [args.llm]

    for llm in llms:
        # Workflow 1
        print(f"\n{'='*80}")
        print(f"WORKFLOW 1 - Feature-Enriched ({llm})")
        print(f"{'='*80}")
        try:
            w1 = workflow1_feature_enriched(
                df, llm_name=llm,
                min_support=MIN_SUPPORT, min_confidence=MIN_CONFIDENCE,
            )
            save_results(w1, f"workflow1_{llm}", dataset_name)
            all_results.append((f"W1-{llm}", w1))
        except Exception as e:
            print(f"Erreur: {e}")

        # Workflow 2
        print(f"\n{'='*80}")
        print(f"WORKFLOW 2 - Guided Search ({llm})")
        print(f"{'='*80}")
        try:
            w2 = workflow2_guided_search(
                df, llm_name=llm,
                min_support=MIN_SUPPORT, min_confidence=MIN_CONFIDENCE,
            )
            save_results(w2, f"workflow2_{llm}", dataset_name)
            all_results.append((f"W2-{llm}", w2))
        except Exception as e:
            print(f"Erreur: {e}")

    # Comparaison
    print(f"\n\n{'='*80}")
    print(f"COMPARAISON - {dataset_name}")
    print(f"{'='*80}")
    print(compare_approaches(all_results))


if __name__ == "__main__":
    main()
