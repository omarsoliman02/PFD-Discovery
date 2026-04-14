"""Module de generation de candidats X -> Y.

Genere toutes les paires (transformation_X, colonne_Y) candidates
pour la decouverte de PFDs.
"""

import pandas as pd
from .pattern_extraction import Transformation, generate_default_transformations


def generate_candidates(
    df: pd.DataFrame,
    transformations: list[Transformation] | None = None,
    target_columns: list[str] | None = None,
) -> list[tuple[Transformation, str]]:
    """Genere toutes les paires (transformation_sur_X, colonne_Y) candidates.

    Args:
        df: DataFrame source
        transformations: Liste de transformations a explorer (defaut: auto-generees)
        target_columns: Colonnes Y cibles (defaut: toutes les colonnes)

    Returns:
        Liste de tuples (Transformation, colonne_Y)
    """
    if transformations is None:
        transformations = generate_default_transformations(df)

    if target_columns is None:
        target_columns = list(df.columns)

    candidates = []
    for transf in transformations:
        for y_col in target_columns:
            # Eviter X -> X (une colonne ne se predit pas elle-meme)
            if transf.name == "identity" and transf.column == y_col:
                continue
            # Eviter de predire la meme colonne transformee
            if transf.column == y_col:
                continue
            candidates.append((transf, y_col))

    return candidates
