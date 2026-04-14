"""Module d'extraction de patterns a partir des valeurs d'attributs.

Transformations supportees :
  - prefix(val, k)     : les k premiers caracteres
  - suffix(val, k)     : les k derniers caracteres
  - first_token(val)   : le premier mot (split sur espaces/virgules)
  - last_token(val)    : le dernier mot
  - tokens(val)        : tous les mots individuels
  - ngram(val, n)      : tous les sous-chaines de longueur n
  - length(val)        : longueur de la chaine
  - numeric_prefix(val, k) : prefixe numerique de k chiffres (pour codes postaux etc.)
"""

import re
import pandas as pd
from dataclasses import dataclass


@dataclass
class Transformation:
    """Represente une transformation appliquee a un attribut."""
    name: str        # ex: "prefix", "first_token"
    column: str      # ex: "zip", "name"
    params: dict     # ex: {"k": 3} pour prefix(zip, 3)

    def __str__(self):
        if self.params:
            param_str = ", ".join(f"{v}" for v in self.params.values())
            return f"{self.name}({self.column}, {param_str})"
        return f"{self.name}({self.column})"

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return str(self) == str(other)


def prefix(value: str, k: int) -> str:
    """Retourne les k premiers caracteres."""
    return value[:k] if len(value) >= k else value


def suffix(value: str, k: int) -> str:
    """Retourne les k derniers caracteres."""
    return value[-k:] if len(value) >= k else value


def first_token(value: str) -> str:
    """Retourne le premier mot (split sur espace, virgule, tiret)."""
    tokens = re.split(r'[,\s\-]+', value.strip())
    return tokens[0] if tokens else value


def last_token(value: str) -> str:
    """Retourne le dernier mot."""
    tokens = re.split(r'[,\s\-]+', value.strip())
    return tokens[-1] if tokens else value


def all_tokens(value: str) -> list[str]:
    """Retourne tous les mots."""
    return [t for t in re.split(r'[,\s\-]+', value.strip()) if t]


def ngrams(value: str, n: int) -> list[str]:
    """Retourne tous les n-grams de la valeur."""
    return [value[i:i+n] for i in range(len(value) - n + 1)]


def length(value: str) -> str:
    """Retourne la longueur de la chaine (comme string pour le groupement)."""
    return str(len(value))


def numeric_prefix(value: str, k: int) -> str:
    """Extrait les k premiers chiffres d'une valeur."""
    digits = re.sub(r'[^0-9]', '', value)
    return digits[:k] if len(digits) >= k else digits


def apply_transformation(df: pd.DataFrame, transf: Transformation) -> pd.Series:
    """Applique une transformation a une colonne du DataFrame et retourne la serie resultante."""
    col = df[transf.column].astype(str)

    if transf.name == "prefix":
        k = transf.params["k"]
        return col.apply(lambda v: prefix(v, k))
    elif transf.name == "suffix":
        k = transf.params["k"]
        return col.apply(lambda v: suffix(v, k))
    elif transf.name == "first_token":
        return col.apply(first_token)
    elif transf.name == "last_token":
        return col.apply(last_token)
    elif transf.name == "length":
        return col.apply(length)
    elif transf.name == "numeric_prefix":
        k = transf.params["k"]
        return col.apply(lambda v: numeric_prefix(v, k))
    elif transf.name == "identity":
        return col
    else:
        raise ValueError(f"Transformation inconnue: {transf.name}")


def generate_default_transformations(df: pd.DataFrame, max_prefix_len: int = 5) -> list[Transformation]:
    """Genere un ensemble de transformations par defaut pour toutes les colonnes."""
    transformations = []

    for col in df.columns:
        non_empty = df[col][df[col].astype(str).str.strip() != ""]
        if len(non_empty) == 0:
            continue

        sample_values = non_empty.astype(str).head(20).tolist()

        # Identity (valeur brute)
        transformations.append(Transformation("identity", col, {}))

        # First/last token (si les valeurs contiennent des espaces)
        has_spaces = any(" " in v or "," in v for v in sample_values)
        if has_spaces:
            transformations.append(Transformation("first_token", col, {}))
            transformations.append(Transformation("last_token", col, {}))

        # Prefixes de differentes longueurs
        avg_len = sum(len(v) for v in sample_values) / len(sample_values)
        for k in range(1, min(int(avg_len), max_prefix_len) + 1):
            transformations.append(Transformation("prefix", col, {"k": k}))

        # Prefixe numerique (si les valeurs contiennent des chiffres)
        has_digits = any(re.search(r'\d', v) for v in sample_values)
        if has_digits:
            for k in range(1, min(6, max_prefix_len + 1)):
                transformations.append(
                    Transformation("numeric_prefix", col, {"k": k})
                )

        # Length
        transformations.append(Transformation("length", col, {}))

    return transformations


def enrich_dataframe(df: pd.DataFrame, transformations: list[Transformation]) -> pd.DataFrame:
    """Enrichit le DataFrame avec des colonnes derivees des transformations."""
    enriched = df.copy()
    for transf in transformations:
        col_name = str(transf)
        enriched[col_name] = apply_transformation(df, transf)
    return enriched
