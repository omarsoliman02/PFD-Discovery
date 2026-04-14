"""Module de validation des PFDs candidates.

Calcule le support et la confidence pour chaque candidat X -> Y,
et filtre par seuils.
"""

import pandas as pd
from dataclasses import dataclass
from .pattern_extraction import Transformation, apply_transformation
from .pattern_grouping import group_by_pattern


@dataclass
class PFDResult:
    """Resultat de validation d'une PFD."""
    x_transformation: Transformation  # Transformation appliquee a X
    y_column: str                     # Colonne cible Y
    support: int                      # Nombre total de tuples couverts
    confidence: float                 # Proportion de tuples coherents
    noise: float                      # 1 - confidence
    num_groups: int                   # Nombre de groupes formes
    details: dict                     # Details par groupe {pattern_val: {y_val: count}}

    def __str__(self):
        return (
            f"{self.x_transformation} -> {self.y_column} "
            f"[support={self.support}, conf={self.confidence:.3f}, "
            f"noise={self.noise:.3f}, groups={self.num_groups}]"
        )


def validate_candidate(
    df: pd.DataFrame,
    x_transf: Transformation,
    y_col: str,
    min_support: int = 2,
) -> PFDResult:
    """Valide un candidat PFD en calculant support et confidence.

    Pour chaque groupe defini par le pattern X :
      - On regarde la valeur la plus frequente de Y dans ce groupe
      - La confidence du groupe = count(valeur_majoritaire) / count(groupe)
    La confidence globale = somme des tuples coherents / somme des tuples couverts
    """
    groups = group_by_pattern(df, x_transf, min_group_size=min_support)

    if not groups:
        return PFDResult(
            x_transformation=x_transf,
            y_column=y_col,
            support=0,
            confidence=0.0,
            noise=1.0,
            num_groups=0,
            details={},
        )

    total_tuples = 0
    consistent_tuples = 0
    details = {}

    for pattern_val, group_df in groups.items():
        y_values = group_df[y_col].astype(str)
        value_counts = y_values.value_counts()
        majority_count = value_counts.iloc[0]
        group_size = len(group_df)

        total_tuples += group_size
        consistent_tuples += majority_count
        details[pattern_val] = value_counts.to_dict()

    confidence = consistent_tuples / total_tuples if total_tuples > 0 else 0.0

    return PFDResult(
        x_transformation=x_transf,
        y_column=y_col,
        support=total_tuples,
        confidence=confidence,
        noise=1.0 - confidence,
        num_groups=len(groups),
        details=details,
    )


def discover_pfds(
    df: pd.DataFrame,
    candidates: list[tuple[Transformation, str]],
    min_support: int = 2,
    min_confidence: float = 0.8,
) -> list[PFDResult]:
    """Decouvre les PFDs valides parmi les candidats.

    Args:
        df: DataFrame source
        candidates: Liste de paires (Transformation, colonne_Y)
        min_support: Support minimum
        min_confidence: Confidence minimum

    Returns:
        Liste des PFDs validees, triees par confidence decroissante
    """
    valid_pfds = []

    for x_transf, y_col in candidates:
        result = validate_candidate(df, x_transf, y_col, min_support)
        if result.support >= min_support and result.confidence >= min_confidence:
            valid_pfds.append(result)

    valid_pfds.sort(key=lambda r: (r.confidence, r.support), reverse=True)
    return valid_pfds
