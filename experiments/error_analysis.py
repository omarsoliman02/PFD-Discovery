"""Analyse d'erreur : pourquoi Mistral W2 manque-t-il des PFDs parfaites ?

Compare les PFDs decouvertes par l'approche classique et par W2-Mistral,
identifie les PFDs parfaites (confidence = 1.0) presentes dans l'approche
classique mais absentes de W2-Mistral, et explique pourquoi :
  - la transformation n'a pas ete suggeree par l'agent
  - la transformation a ete suggeree mais le candidat X -> Y n'a pas ete priorise
  - le candidat a ete priorise mais filtre par le seuil

Usage:
  python3 experiments/error_analysis.py --dataset t1
  python3 experiments/error_analysis.py --dataset t1 --llm mistral
"""

import sys
import os
import json
import argparse
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.data_loader import load_csv, list_datasets
from src.classical_pipeline import run_classical_pipeline
from src.agentic_workflow import workflow2_guided_search


def find_dataset(data_dir: str, name: str) -> str | None:
    datasets = list_datasets(data_dir)
    for folder, files in datasets.items():
        for fp in files:
            if name in os.path.basename(fp):
                return fp
    return None


def signature(pfd) -> str:
    return f"{pfd.x_transformation} -> {pfd.y_column}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--llm", default="mistral", choices=["mistral", "llama"])
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
    print(f"LLM teste: {args.llm}")
    print(f"Seuils: K={args.min_support}, theta={args.min_confidence}")
    print()

    # 1. Approche classique
    print("=" * 80)
    print("[1/2] Approche classique")
    print("=" * 80)
    classical = run_classical_pipeline(
        df,
        min_support=args.min_support,
        min_confidence=args.min_confidence,
        verbose=False,
    )
    classical_perfect = [p for p in classical["generalized"] if p.confidence >= 1.0]
    print(f"Total PFDs (generalisees) : {len(classical['generalized'])}")
    print(f"PFDs parfaites (conf = 1.0) : {len(classical_perfect)}")
    for p in classical_perfect:
        print(f"  - {p}")

    # 2. W2 avec LLM
    print()
    print("=" * 80)
    print(f"[2/2] Workflow 2 ({args.llm})")
    print("=" * 80)
    w2 = workflow2_guided_search(
        df,
        llm_name=args.llm,
        min_support=args.min_support,
        min_confidence=args.min_confidence,
        verbose=False,
    )
    w2_perfect = [p for p in w2["generalized"] if p.confidence >= 1.0]
    w2_signatures = {signature(p) for p in w2["generalized"]}
    print(f"Total PFDs (generalisees) : {len(w2['generalized'])}")
    print(f"PFDs parfaites (conf = 1.0) : {len(w2_perfect)}")
    for p in w2_perfect:
        print(f"  - {p}")

    # === Analyse d'erreur ===
    print()
    print("=" * 80)
    print("ANALYSE D'ERREUR : PFDs parfaites manquees par W2")
    print("=" * 80)

    missed = [p for p in classical_perfect if signature(p) not in w2_signatures]
    print(f"\nPFDs parfaites trouvees par CLASSIQUE mais MANQUEES par W2-{args.llm} : {len(missed)}")
    print()

    # Pour chaque PFD manquee, identifier la cause
    suggested_transformations = [str(t) for t in w2.get("agent_transformations", [])]
    prioritized_candidates = w2.get("prioritized_candidates", [])
    prioritized_pairs = {
        f"{c.get('x_transformation', '')} -> {c.get('y_column', '')}"
        for c in prioritized_candidates
    }

    error_breakdown = {
        "transformation_missing": [],
        "candidate_not_prioritized": [],
        "filtered_out": [],
    }

    for p in missed:
        transf_str = str(p.x_transformation)
        cand_str = signature(p)

        # Cause 1 : la transformation X n'a pas ete suggeree
        if transf_str not in suggested_transformations:
            cause = "transformation_missing"
            reason = (
                f"La transformation '{transf_str}' n'a pas ete suggeree par {args.llm} "
                f"dans la phase 1 (suggest_transformations). "
                f"=> Le LLM n'a pas identifie cette colonne comme candidate de PFD."
            )
        # Cause 2 : la transformation existe mais la paire X -> Y n'a pas ete priorisee
        elif cand_str not in prioritized_pairs:
            cause = "candidate_not_prioritized"
            reason = (
                f"La transformation '{transf_str}' a ete suggeree, mais le candidat "
                f"'{cand_str}' n'a pas ete selectionne par {args.llm} "
                f"dans la phase 2 (prioritize_candidates). "
                f"=> Le LLM n'a pas juge cette paire semantiquement interessante."
            )
        # Cause 3 : la paire a ete priorisee mais a echoue au filtre support/confidence
        else:
            cause = "filtered_out"
            reason = (
                f"La paire '{cand_str}' a ete priorisee mais a ete filtree par les "
                f"seuils (support>={args.min_support}, conf>={args.min_confidence})."
            )

        error_breakdown[cause].append({
            "pfd": str(p),
            "transformation": transf_str,
            "y_column": p.y_column,
            "support": p.support,
            "confidence": p.confidence,
            "reason": reason,
        })
        print(f"PFD manquee : {p}")
        print(f"  Cause : {cause}")
        print(f"  Detail : {reason}")
        print()

    # === Synthese ===
    print("=" * 80)
    print("SYNTHESE DE L'ANALYSE")
    print("=" * 80)
    print(f"Transformations suggerees par {args.llm} : {len(suggested_transformations)}")
    for t in suggested_transformations:
        print(f"  - {t}")
    print()
    print(f"Candidats priorises par {args.llm} : {len(prioritized_candidates)}")
    for c in prioritized_candidates:
        print(f"  - {c.get('x_transformation')} -> {c.get('y_column')} [{c.get('priority', 'N/A')}]")
    print()
    print(f"Causes d'erreur :")
    print(f"  - Transformation jamais suggeree     : {len(error_breakdown['transformation_missing'])}")
    print(f"  - Transformation OK mais paire non priorisee : {len(error_breakdown['candidate_not_prioritized'])}")
    print(f"  - Paire priorisee mais filtree par seuil     : {len(error_breakdown['filtered_out'])}")

    # Sauvegarde JSON
    output_path = os.path.join(
        os.path.dirname(__file__), "..", "results",
        f"error_analysis_{args.llm}_{dataset_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
    )
    summary = {
        "dataset": dataset_name,
        "llm": args.llm,
        "min_support": args.min_support,
        "min_confidence": args.min_confidence,
        "classical_perfect_count": len(classical_perfect),
        "classical_perfect": [str(p) for p in classical_perfect],
        "w2_perfect_count": len(w2_perfect),
        "w2_perfect": [str(p) for p in w2_perfect],
        "missed_count": len(missed),
        "suggested_transformations": suggested_transformations,
        "prioritized_candidates": prioritized_candidates,
        "error_breakdown": error_breakdown,
    }
    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\nAnalyse sauvegardee : {output_path}")


if __name__ == "__main__":
    main()
