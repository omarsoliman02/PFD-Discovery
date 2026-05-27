"""Execute le Workflow 3 (Agent-in-the-Loop) sur un dataset.

Usage:
  python3 experiments/run_workflow3.py --dataset t1 --llm mistral
  python3 experiments/run_workflow3.py --dataset US_Phone_Code --llm llama --iterations 3
"""

import sys
import os
import argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.data_loader import load_csv, list_datasets
from src.agentic_workflow import workflow3_agent_in_the_loop
from src.evaluation import save_results, compute_metrics


def find_dataset(data_dir: str, name: str) -> str | None:
    datasets = list_datasets(data_dir)
    for folder, files in datasets.items():
        for fp in files:
            if name in os.path.basename(fp):
                return fp
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--llm", default="mistral", choices=["mistral", "llama"])
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument("--min-support", type=int, default=5)
    parser.add_argument("--min-confidence", type=float, default=0.85)
    args = parser.parse_args()

    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    filepath = find_dataset(data_dir, args.dataset)
    if not filepath:
        print(f"Dataset '{args.dataset}' introuvable")
        sys.exit(1)

    dataset_name = os.path.basename(filepath).replace(".csv", "")
    df = load_csv(filepath)
    print(f"Dataset: {dataset_name} ({df.shape[0]} lignes, {df.shape[1]} colonnes)")
    print()

    results = workflow3_agent_in_the_loop(
        df,
        llm_name=args.llm,
        min_support=args.min_support,
        min_confidence=args.min_confidence,
        max_iterations=args.iterations,
    )

    # Sauvegarde -- on serialise aussi le journal d'iterations
    save_path = save_results(results, f"workflow3_{args.llm}", dataset_name)

    # Ajouter le iteration_log au JSON sauvegarde
    import json
    with open(save_path, "r") as f:
        data = json.load(f)
    data["iteration_log"] = results.get("iteration_log", [])
    data["num_iterations"] = results.get("num_iterations", 0)
    with open(save_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nResultats sauvegardes: {save_path}")

    # Resume
    metrics = compute_metrics(results, f"workflow3_{args.llm}")
    print()
    print("=" * 80)
    print("RESUME")
    print("=" * 80)
    print(f"Iterations executees   : {results['num_iterations']}")
    print(f"Hypotheses totales     : {results['num_candidates']}")
    print(f"PFDs acceptees         : {metrics['num_pfds']}")
    print(f"PFDs parfaites         : {metrics['num_perfect']}")
    print(f"Confidence moyenne     : {metrics['avg_confidence']}")
    print(f"Temps d'execution      : {metrics['execution_time']}s")


if __name__ == "__main__":
    main()
