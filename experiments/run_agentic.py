"""Script pour executer les workflows agentiques sur tous les datasets.

Usage:
  python run_agentic.py                        # Tous les datasets, modeles locaux
  python run_agentic.py --llm mistral          # Seulement Mistral (local)
  python run_agentic.py --llm llama            # Seulement Llama (local)
  python run_agentic.py --llm gemini           # Seulement Gemini (API)
  python run_agentic.py --llm cohere           # Seulement Cohere (API)
  python run_agentic.py --dataset t1           # Seulement le dataset t1
  python run_agentic.py --workflow 1           # Seulement Workflow 1

Modeles locaux (Ollama, sans quota) : mistral, llama
Modeles cloud (API, avec quota) : gemini, cohere
"""

import sys
import os
import argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.data_loader import load_csv, list_datasets
from src.agentic_workflow import workflow1_feature_enriched, workflow2_guided_search
from src.evaluation import compute_metrics, save_results, compare_approaches

MIN_SUPPORT = 5
MIN_CONFIDENCE = 0.85


def main():
    parser = argparse.ArgumentParser(description="Executer les workflows agentiques")
    parser.add_argument("--llm", choices=["mistral", "llama", "gemini", "cohere", "local", "all"], default="local")
    parser.add_argument("--dataset", type=str, default=None, help="Nom du dataset (ex: t1, US_Phone_Code)")
    parser.add_argument("--workflow", type=int, choices=[1, 2], default=None, help="Numero du workflow")
    args = parser.parse_args()

    if args.llm == "local":
        llms = ["mistral", "llama"]
    elif args.llm == "all":
        llms = ["mistral", "llama", "gemini", "cohere"]
    else:
        llms = [args.llm]
    workflows = [1, 2] if args.workflow is None else [args.workflow]

    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    datasets = list_datasets(data_dir)

    all_approach_results = []

    for folder, files in datasets.items():
        for filepath in files:
            dataset_name = os.path.basename(filepath).replace(".csv", "")

            # Filtre par dataset si specifie
            if args.dataset and args.dataset not in dataset_name:
                continue

            print(f"\n{'='*80}")
            print(f"Dataset: {folder}/{dataset_name}")
            print(f"{'='*80}")

            df = load_csv(filepath)
            print(f"Shape: {df.shape}")

            for llm in llms:
                for wf_num in workflows:
                    approach_name = f"workflow{wf_num}_{llm}"
                    print(f"\n--- {approach_name} ---")

                    try:
                        if wf_num == 1:
                            results = workflow1_feature_enriched(
                                df, llm_name=llm,
                                min_support=MIN_SUPPORT,
                                min_confidence=MIN_CONFIDENCE,
                            )
                        else:
                            results = workflow2_guided_search(
                                df, llm_name=llm,
                                min_support=MIN_SUPPORT,
                                min_confidence=MIN_CONFIDENCE,
                            )

                        save_path = save_results(
                            results, approach_name, f"{folder}_{dataset_name}"
                        )
                        print(f"Resultats sauvegardes: {save_path}")

                        all_approach_results.append(
                            (f"{approach_name}/{folder}/{dataset_name}", results)
                        )

                    except Exception as e:
                        print(f"ERREUR: {e}")
                        continue

    # Comparaison globale
    if all_approach_results:
        print(f"\n\n{'='*80}")
        print("COMPARAISON GLOBALE")
        print(f"{'='*80}")
        print(compare_approaches(all_approach_results))


if __name__ == "__main__":
    main()
