"""Pipeline classique complet de decouverte de PFDs.

Enchaine les 5 etapes :
  1. Extraction de patterns
  2. Groupement
  3. Generation de candidats
  4. Validation
  5. Generalisation
"""

import time
import pandas as pd
from .pattern_extraction import Transformation, generate_default_transformations
from .candidate_generation import generate_candidates
from .validation import discover_pfds, PFDResult
from .generalization import generalize_pfds


def run_classical_pipeline(
    df: pd.DataFrame,
    min_support: int = 2,
    min_confidence: float = 0.8,
    max_prefix_len: int = 5,
    transformations: list[Transformation] | None = None,
    target_columns: list[str] | None = None,
    verbose: bool = True,
) -> dict:
    """Execute le pipeline classique complet.

    Args:
        df: DataFrame source
        min_support: Support minimum pour filtrer
        min_confidence: Confidence minimum pour filtrer
        max_prefix_len: Longueur max des prefixes a explorer
        transformations: Transformations a utiliser (defaut: auto-generees)
        target_columns: Colonnes cibles Y (defaut: toutes)
        verbose: Afficher les infos de progression

    Returns:
        Dictionnaire avec les resultats :
        {
            "pfds": list[PFDResult],           # PFDs validees
            "generalized": list[PFDResult],    # PFDs generalisees
            "num_candidates": int,
            "num_valid": int,
            "num_generalized": int,
            "execution_time": float,
        }
    """
    start_time = time.time()

    # Etape 1 : Generation des transformations
    if transformations is None:
        transformations = generate_default_transformations(df, max_prefix_len)
    if verbose:
        print(f"[1/5] Extraction: {len(transformations)} transformations generees")

    # Etape 2-3 : Generation des candidats (inclut le groupement implicitement)
    candidates = generate_candidates(df, transformations, target_columns)
    if verbose:
        print(f"[2-3/5] Candidats: {len(candidates)} paires X -> Y a evaluer")

    # Etape 4 : Validation
    valid_pfds = discover_pfds(df, candidates, min_support, min_confidence)
    if verbose:
        print(f"[4/5] Validation: {len(valid_pfds)} PFDs valides trouvees")

    # Etape 5 : Generalisation
    generalized = generalize_pfds(valid_pfds)
    if verbose:
        print(f"[5/5] Generalisation: {len(generalized)} PFDs apres generalisation")

    elapsed = time.time() - start_time
    if verbose:
        print(f"\nTemps d'execution: {elapsed:.2f}s")
        print(f"\n--- Top PFDs decouvertes ---")
        for pfd in generalized[:15]:
            print(f"  {pfd}")

    return {
        "pfds": valid_pfds,
        "generalized": generalized,
        "num_candidates": len(candidates),
        "num_valid": len(valid_pfds),
        "num_generalized": len(generalized),
        "execution_time": elapsed,
    }
