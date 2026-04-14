"""Module de groupement de tuples par pattern.

Regroupe les lignes d'un DataFrame qui partagent la meme valeur
apres application d'une transformation.
"""

import pandas as pd
from .pattern_extraction import Transformation, apply_transformation


def group_by_pattern(
    df: pd.DataFrame,
    transf: Transformation,
    min_group_size: int = 2,
) -> dict[str, pd.DataFrame]:
    """Regroupe les tuples par valeur du pattern.

    Args:
        df: DataFrame source
        transf: Transformation a appliquer
        min_group_size: Taille minimale d'un groupe (filtre le bruit)

    Returns:
        Dictionnaire {valeur_pattern: sous-DataFrame}
    """
    pattern_values = apply_transformation(df, transf)

    # Filtrer les valeurs vides
    mask = pattern_values.str.strip() != ""
    df_filtered = df[mask].copy()
    pattern_values = pattern_values[mask]

    groups = {}
    for pattern_val, group_df in df_filtered.groupby(pattern_values):
        if len(group_df) >= min_group_size:
            groups[pattern_val] = group_df

    return groups
