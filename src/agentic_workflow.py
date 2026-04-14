"""Workflows agentiques pour la decouverte de PFDs.

Workflow 1 : Feature-Enriched Discovery
  - L'agent suggere les transformations, l'algo classique fait le reste

Workflow 2 : Guided Search
  - L'agent suggere les transformations ET priorise les candidats
  - L'algo ne valide que les candidats selectionnes
"""

import re
import time
import pandas as pd

from .data_loader import get_schema_info
from .pattern_extraction import Transformation, generate_default_transformations
from .candidate_generation import generate_candidates
from .validation import discover_pfds, PFDResult
from .generalization import generalize_pfds
from .llm_agent import (
    suggest_transformations,
    prioritize_candidates,
    format_schema_for_prompt,
)


def _parse_transformation_suggestion(suggestion: dict) -> Transformation | None:
    """Convertit une suggestion LLM en objet Transformation."""
    name = suggestion.get("name", "").lower().strip()
    column = suggestion.get("column", "").strip()
    params = suggestion.get("params", {})

    if not name or not column:
        return None

    # Normaliser les noms de transformations
    name_map = {
        "prefix": "prefix",
        "suffix": "suffix",
        "first_token": "first_token",
        "last_token": "last_token",
        "numeric_prefix": "numeric_prefix",
        "identity": "identity",
        "length": "length",
    }

    if name not in name_map:
        return None

    return Transformation(name=name_map[name], column=column, params=params)


def _parse_candidate_string(candidate_str: str, columns: list[str]) -> tuple[Transformation, str] | None:
    """Parse une string comme 'prefix(ZIP, 3) -> CITY' en (Transformation, y_col)."""
    # Essayer de parser "transf(col, params) -> y_col"
    match = re.match(
        r'(\w+)\((\w[\w\s]*?)(?:,\s*(\d+))?\)\s*->\s*(\w[\w\s]*)',
        candidate_str.strip()
    )
    if not match:
        return None

    t_name = match.group(1).lower()
    t_col = match.group(2).strip()
    t_param = match.group(3)
    y_col = match.group(4).strip()

    params = {}
    if t_param is not None:
        params["k"] = int(t_param)

    # Verifier que la colonne cible existe (correspondance insensible a la casse)
    col_map = {c.lower(): c for c in columns}
    actual_t_col = col_map.get(t_col.lower())
    actual_y_col = col_map.get(y_col.lower())

    if actual_t_col is None or actual_y_col is None:
        return None

    transf = Transformation(name=t_name, column=actual_t_col, params=params)
    return (transf, actual_y_col)


def workflow1_feature_enriched(
    df: pd.DataFrame,
    llm_name: str = "claude",
    api_key: str | None = None,
    min_support: int = 2,
    min_confidence: float = 0.8,
    verbose: bool = True,
) -> dict:
    """Workflow 1 : Feature-Enriched Discovery.

    1. L'agent analyse le schema et suggere des transformations
    2. On genere les features correspondantes
    3. L'algorithme classique decouvre les PFDs

    Returns:
        Resultats incluant PFDs, suggestions de l'agent, metriques
    """
    start_time = time.time()

    # Etape 1 : Obtenir les infos de schema
    schema_info = get_schema_info(df)
    if verbose:
        print(f"[W1-1] Schema analyse: {len(df.columns)} colonnes, {len(df)} lignes")

    # Etape 2 : Demander au LLM de suggerer des transformations
    if verbose:
        print(f"[W1-2] Interrogation du LLM ({llm_name})...")
    suggestions = suggest_transformations(schema_info, llm_name, api_key)
    if verbose:
        print(f"[W1-2] {len(suggestions)} transformations suggerees par {llm_name}")
        for s in suggestions:
            print(f"  - {s.get('name')}({s.get('column')}, {s.get('params', {})}) : {s.get('reason', '')[:80]}")

    # Etape 3 : Convertir les suggestions en objets Transformation
    agent_transformations = []
    for s in suggestions:
        transf = _parse_transformation_suggestion(s)
        if transf and transf.column in df.columns:
            agent_transformations.append(transf)

    if verbose:
        print(f"[W1-3] {len(agent_transformations)} transformations valides retenues")

    if not agent_transformations:
        if verbose:
            print("[W1-3] Aucune transformation valide, fallback sur les transformations par defaut")
        agent_transformations = generate_default_transformations(df)

    # Etape 4 : Generer les candidats et decouvrir les PFDs
    candidates = generate_candidates(df, agent_transformations)
    if verbose:
        print(f"[W1-4] {len(candidates)} candidats generes")

    valid_pfds = discover_pfds(df, candidates, min_support, min_confidence)
    generalized = generalize_pfds(valid_pfds)

    elapsed = time.time() - start_time
    if verbose:
        print(f"[W1-5] {len(valid_pfds)} PFDs valides, {len(generalized)} apres generalisation")
        print(f"\nTemps d'execution: {elapsed:.2f}s")
        print(f"\n--- Top PFDs (Workflow 1 - {llm_name}) ---")
        for pfd in generalized[:15]:
            print(f"  {pfd}")

    return {
        "pfds": valid_pfds,
        "generalized": generalized,
        "agent_suggestions": suggestions,
        "agent_transformations": [str(t) for t in agent_transformations],
        "num_candidates": len(candidates),
        "num_valid": len(valid_pfds),
        "num_generalized": len(generalized),
        "execution_time": elapsed,
        "llm_name": llm_name,
    }


def workflow2_guided_search(
    df: pd.DataFrame,
    llm_name: str = "claude",
    api_key: str | None = None,
    min_support: int = 2,
    min_confidence: float = 0.8,
    verbose: bool = True,
) -> dict:
    """Workflow 2 : Guided Search.

    1. L'agent suggere des transformations (comme Workflow 1)
    2. L'agent priorise aussi les candidats X -> Y
    3. L'algo ne valide que les candidats selectionnes par l'agent

    Returns:
        Resultats incluant PFDs, suggestions, candidats priorises, metriques
    """
    start_time = time.time()

    # Etape 1 : Schema
    schema_info = get_schema_info(df)
    if verbose:
        print(f"[W2-1] Schema analyse: {len(df.columns)} colonnes, {len(df)} lignes")

    # Etape 2 : Suggestions de transformations
    if verbose:
        print(f"[W2-2] Interrogation du LLM ({llm_name}) pour les transformations...")
    suggestions = suggest_transformations(schema_info, llm_name, api_key)

    agent_transformations = []
    for s in suggestions:
        transf = _parse_transformation_suggestion(s)
        if transf and transf.column in df.columns:
            agent_transformations.append(transf)

    if not agent_transformations:
        agent_transformations = generate_default_transformations(df)

    if verbose:
        print(f"[W2-2] {len(agent_transformations)} transformations retenues")

    # Etape 3 : Priorisation des candidats par l'agent
    transf_strings = [str(t) for t in agent_transformations]
    if verbose:
        print(f"[W2-3] Interrogation du LLM ({llm_name}) pour prioriser les candidats...")

    prioritized = prioritize_candidates(schema_info, transf_strings, llm_name, api_key)

    if verbose:
        print(f"[W2-3] {len(prioritized)} candidats priorises par {llm_name}")
        for c in prioritized:
            print(f"  - {c.get('x_transformation')} -> {c.get('y_column')} [{c.get('priority')}] : {c.get('reason', '')[:60]}")

    # Etape 4 : Convertir les candidats priorises en paires (Transformation, y_col)
    selected_candidates = []
    for c in prioritized:
        x_str = c.get("x_transformation", "")
        y_col = c.get("y_column", "")
        parsed = _parse_candidate_string(f"{x_str} -> {y_col}", list(df.columns))
        if parsed:
            selected_candidates.append(parsed)

    # Ajouter aussi les identity transforms pour les colonnes categoriques
    for transf in agent_transformations:
        if transf.name == "identity":
            for col in df.columns:
                if col != transf.column:
                    selected_candidates.append((transf, col))

    if verbose:
        print(f"[W2-4] {len(selected_candidates)} candidats retenus pour validation")

    if not selected_candidates:
        if verbose:
            print("[W2-4] Aucun candidat valide, fallback sur generation complete")
        selected_candidates = generate_candidates(df, agent_transformations)

    # Etape 5 : Validation
    valid_pfds = discover_pfds(df, selected_candidates, min_support, min_confidence)
    generalized = generalize_pfds(valid_pfds)

    elapsed = time.time() - start_time
    if verbose:
        print(f"[W2-5] {len(valid_pfds)} PFDs valides, {len(generalized)} apres generalisation")
        print(f"\nTemps d'execution: {elapsed:.2f}s")
        print(f"\n--- Top PFDs (Workflow 2 - {llm_name}) ---")
        for pfd in generalized[:15]:
            print(f"  {pfd}")

    return {
        "pfds": valid_pfds,
        "generalized": generalized,
        "agent_suggestions": suggestions,
        "agent_transformations": transf_strings,
        "prioritized_candidates": prioritized,
        "num_candidates": len(selected_candidates),
        "num_valid": len(valid_pfds),
        "num_generalized": len(generalized),
        "execution_time": elapsed,
        "llm_name": llm_name,
    }
