"""Compare la generalisation algorithmique a la generalisation semantique par LLM.

Sur un dataset, on execute le pipeline classique jusqu'a l'etape 4 (validation),
puis on applique les deux strategies de generalisation :
  - generalize_pfds (algorithmique)
  - generalize_pfds_llm (semantique via LLM)

Usage:
  python3 experiments/run_llm_generalization.py --dataset t1 --llm mistral
"""

import sys
import os
import json
import argparse
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.data_loader import load_csv, list_datasets, get_schema_info
from src.pattern_extraction import generate_default_transformations
from src.candidate_generation import generate_candidates
from src.validation import discover_pfds
from src.generalization import generalize_pfds, generalize_pfds_llm


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
    schema = get_schema_info(df)
    print(f"Dataset: {dataset_name} ({df.shape[0]} lignes, {df.shape[1]} colonnes)")
    print()

    # Pipeline jusqu'a l'etape 4
    print("[1-4] Execution du pipeline classique jusqu'a la validation...")
    transformations = generate_default_transformations(df, max_prefix_len=4)
    candidates = generate_candidates(df, transformations)
    valid_pfds = discover_pfds(
        df, candidates,
        min_support=args.min_support,
        min_confidence=args.min_confidence,
    )
    print(f"  {len(transformations)} transformations, {len(candidates)} candidats, {len(valid_pfds)} PFDs validees")
    print()

    # Limiter pour ne pas saturer le LLM (Mistral 7B sur CPU est lent)
    MAX_PFDS_FOR_LLM = 30
    if len(valid_pfds) > MAX_PFDS_FOR_LLM:
        print(f"[!] {len(valid_pfds)} PFDs validees -- on ne passe que les {MAX_PFDS_FOR_LLM} meilleures au LLM (par confidence)")
        valid_pfds_for_llm = valid_pfds[:MAX_PFDS_FOR_LLM]
    else:
        valid_pfds_for_llm = valid_pfds

    # Generalisation algorithmique
    print("[5a] Generalisation algorithmique (shortest prefix / subsomption identity / deduplication)...")
    algo_generalized = generalize_pfds(valid_pfds)
    print(f"  Algorithmique : {len(valid_pfds)} -> {len(algo_generalized)} PFDs")
    print()

    # Generalisation par LLM
    print(f"[5b] Generalisation semantique par LLM ({args.llm})...")
    llm_generalized, llm_groups = generalize_pfds_llm(
        valid_pfds_for_llm, schema, args.llm, verbose=True,
    )
    print(f"  LLM : {len(valid_pfds_for_llm)} -> {len(llm_generalized)} PFDs ({len(llm_groups)} groupes)")
    print()

    # === Affichage des groupes formes par le LLM ===
    print("=" * 80)
    print(f"GROUPES SEMANTIQUES FORMES PAR {args.llm.upper()}")
    print("=" * 80)
    for i, g in enumerate(llm_groups, 1):
        print(f"\nGroupe {i} : \"{g.get('concept', '')}\"")
        print(f"  Representant : {g.get('representative', '')}")
        members = g.get("members", [])
        if len(members) > 1:
            print(f"  Membres ({len(members)}) :")
            for m in members:
                print(f"    - {m}")

    # === Comparaison top 15 ===
    print()
    print("=" * 80)
    print("COMPARAISON TOP 15")
    print("=" * 80)
    print()
    print("--- Algorithmique ---")
    for p in algo_generalized[:15]:
        print(f"  {p}")
    print()
    print(f"--- LLM ({args.llm}) ---")
    for p in llm_generalized[:15]:
        print(f"  {p}")

    # Sauvegarde
    output_path = os.path.join(
        os.path.dirname(__file__), "..", "results",
        f"llm_generalization_{args.llm}_{dataset_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
    )
    summary = {
        "dataset": dataset_name,
        "llm": args.llm,
        "num_valid_pfds": len(valid_pfds),
        "num_algo_generalized": len(algo_generalized),
        "num_llm_generalized": len(llm_generalized),
        "num_semantic_groups": len(llm_groups),
        "algo_generalized": [str(p) for p in algo_generalized],
        "llm_generalized": [str(p) for p in llm_generalized],
        "llm_groups": llm_groups,
    }
    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\nSauvegarde : {output_path}")


if __name__ == "__main__":
    main()
