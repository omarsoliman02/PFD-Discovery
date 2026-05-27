"""Analyse de sensibilite des seuils K (support) et theta (confidence).

Pour chaque combinaison (K, theta), on execute :
  - l'approche classique
  - le workflow 1 (Feature-Enriched)
  - le workflow 2 (Guided Search)

Et on compare le nombre de PFDs decouvertes ainsi que la confidence moyenne.

Usage:
  python3 experiments/sensitivity_analysis.py --dataset t1
  python3 experiments/sensitivity_analysis.py --dataset t1 --thetas 0.85,0.90,0.95,1.0
  python3 experiments/sensitivity_analysis.py --dataset t1 --supports 5,10,20
"""

import sys
import os
import json
import argparse
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.data_loader import load_csv, list_datasets
from src.classical_pipeline import run_classical_pipeline
from src.agentic_workflow import workflow1_feature_enriched, workflow2_guided_search


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
    parser.add_argument(
        "--thetas",
        default="0.85,0.90,0.95,1.00",
        help="Liste des theta a tester, separes par des virgules",
    )
    parser.add_argument(
        "--supports",
        default="5",
        help="Liste des K (support) a tester, separes par des virgules",
    )
    parser.add_argument(
        "--include-agentic",
        action="store_true",
        help="Inclure W1 et W2 (lent : ~1-2 min par theta par LLM)",
    )
    parser.add_argument("--llm", default="mistral", choices=["mistral", "llama"])
    args = parser.parse_args()

    thetas = [float(t) for t in args.thetas.split(",")]
    supports = [int(k) for k in args.supports.split(",")]

    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    filepath = find_dataset(data_dir, args.dataset)
    if not filepath:
        print(f"Dataset '{args.dataset}' introuvable")
        sys.exit(1)

    dataset_name = os.path.basename(filepath).replace(".csv", "")
    df = load_csv(filepath)
    print(f"Dataset: {dataset_name} ({df.shape[0]} lignes, {df.shape[1]} colonnes)")
    print(f"Thetas testes: {thetas}")
    print(f"Supports testes: {supports}")
    print(f"Agentique inclus: {args.include_agentic}")
    print()

    results = []

    for K in supports:
        for theta in thetas:
            print(f"{'='*80}")
            print(f"  K = {K}, theta = {theta}")
            print(f"{'='*80}")

            row = {"K": K, "theta": theta}

            # Classique
            print(f"\n[Classique]")
            classical = run_classical_pipeline(
                df, min_support=K, min_confidence=theta, verbose=False,
            )
            n_pfds = len(classical["generalized"])
            n_perfect = sum(1 for p in classical["generalized"] if p.confidence >= 1.0)
            avg_conf = (
                sum(p.confidence for p in classical["generalized"]) / n_pfds
                if n_pfds else 0.0
            )
            print(f"  PFDs: {n_pfds} (parfaites: {n_perfect}), conf.moy = {avg_conf:.4f}, temps = {classical['execution_time']:.2f}s")
            row["classical_pfds"] = n_pfds
            row["classical_perfect"] = n_perfect
            row["classical_avg_conf"] = round(avg_conf, 4)
            row["classical_time"] = round(classical["execution_time"], 2)

            if args.include_agentic:
                print(f"\n[Workflow 1 - {args.llm}]")
                try:
                    w1 = workflow1_feature_enriched(
                        df, llm_name=args.llm,
                        min_support=K, min_confidence=theta, verbose=False,
                    )
                    n_pfds = len(w1["generalized"])
                    n_perfect = sum(1 for p in w1["generalized"] if p.confidence >= 1.0)
                    avg_conf = (
                        sum(p.confidence for p in w1["generalized"]) / n_pfds
                        if n_pfds else 0.0
                    )
                    print(f"  PFDs: {n_pfds} (parfaites: {n_perfect}), conf.moy = {avg_conf:.4f}, temps = {w1['execution_time']:.2f}s")
                    row["w1_pfds"] = n_pfds
                    row["w1_perfect"] = n_perfect
                    row["w1_avg_conf"] = round(avg_conf, 4)
                    row["w1_time"] = round(w1["execution_time"], 2)
                except Exception as e:
                    print(f"  W1 erreur: {e}")
                    row["w1_pfds"] = None

                print(f"\n[Workflow 2 - {args.llm}]")
                try:
                    w2 = workflow2_guided_search(
                        df, llm_name=args.llm,
                        min_support=K, min_confidence=theta, verbose=False,
                    )
                    n_pfds = len(w2["generalized"])
                    n_perfect = sum(1 for p in w2["generalized"] if p.confidence >= 1.0)
                    avg_conf = (
                        sum(p.confidence for p in w2["generalized"]) / n_pfds
                        if n_pfds else 0.0
                    )
                    print(f"  PFDs: {n_pfds} (parfaites: {n_perfect}), conf.moy = {avg_conf:.4f}, temps = {w2['execution_time']:.2f}s")
                    row["w2_pfds"] = n_pfds
                    row["w2_perfect"] = n_perfect
                    row["w2_avg_conf"] = round(avg_conf, 4)
                    row["w2_time"] = round(w2["execution_time"], 2)
                except Exception as e:
                    print(f"  W2 erreur: {e}")
                    row["w2_pfds"] = None

            results.append(row)
            print()

    # === Tableau final ===
    print(f"\n{'='*100}")
    print(f"RESUME - Analyse de sensibilite ({dataset_name})")
    print(f"{'='*100}")

    if args.include_agentic:
        header = f"{'K':>4} {'theta':>6} | {'C-PFDs':>7} {'C-Parf.':>7} {'C-Conf':>8} | {'W1-PFDs':>8} {'W1-Conf':>8} | {'W2-PFDs':>8} {'W2-Conf':>8}"
    else:
        header = f"{'K':>4} {'theta':>6} | {'C-PFDs':>7} {'C-Parf.':>7} {'C-Conf':>8} {'C-Temps':>8}"
    print(header)
    print("-" * len(header))

    for r in results:
        if args.include_agentic:
            line = (
                f"{r['K']:>4} {r['theta']:>6.2f} | "
                f"{r['classical_pfds']:>7} {r['classical_perfect']:>7} {r['classical_avg_conf']:>8.4f} | "
            )
            if r.get("w1_pfds") is not None:
                line += f"{r['w1_pfds']:>8} {r['w1_avg_conf']:>8.4f} | "
            else:
                line += f"{'N/A':>8} {'N/A':>8} | "
            if r.get("w2_pfds") is not None:
                line += f"{r['w2_pfds']:>8} {r['w2_avg_conf']:>8.4f}"
            else:
                line += f"{'N/A':>8} {'N/A':>8}"
        else:
            line = (
                f"{r['K']:>4} {r['theta']:>6.2f} | "
                f"{r['classical_pfds']:>7} {r['classical_perfect']:>7} "
                f"{r['classical_avg_conf']:>8.4f} {r['classical_time']:>8.2f}"
            )
        print(line)

    # Sauvegarde JSON
    output_path = os.path.join(
        os.path.dirname(__file__), "..", "results",
        f"sensitivity_{dataset_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
    )
    with open(output_path, "w") as f:
        json.dump({
            "dataset": dataset_name,
            "thetas": thetas,
            "supports": supports,
            "include_agentic": args.include_agentic,
            "llm": args.llm if args.include_agentic else None,
            "results": results,
        }, f, indent=2)
    print(f"\nResultats sauvegardes: {output_path}")


if __name__ == "__main__":
    main()
