"""Module de chargement et preprocessing des fichiers CSV."""

import os
import pandas as pd


def load_csv(file_path: str) -> pd.DataFrame:
    """Charge un fichier CSV et retourne un DataFrame pandas."""
    df = pd.read_csv(file_path, dtype=str, keep_default_na=False)
    df.columns = df.columns.str.strip()
    return df


def get_sample(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """Retourne un echantillon de n lignes du DataFrame."""
    return df.head(n)


def get_schema_info(df: pd.DataFrame) -> dict:
    """Retourne les informations de schema : noms de colonnes + types + echantillons de valeurs."""
    info = {}
    for col in df.columns:
        non_empty = df[col][df[col] != ""]
        sample_values = non_empty.head(5).tolist()
        info[col] = {
            "num_rows": len(df),
            "num_unique": non_empty.nunique(),
            "sample_values": sample_values,
        }
    return info


def list_datasets(data_dir: str) -> dict[str, list[str]]:
    """Liste tous les datasets disponibles, organises par sous-dossier."""
    datasets = {}
    for folder in sorted(os.listdir(data_dir)):
        folder_path = os.path.join(data_dir, folder)
        if os.path.isdir(folder_path):
            csv_files = sorted(
                f for f in os.listdir(folder_path) if f.endswith(".csv")
            )
            datasets[folder] = [
                os.path.join(folder_path, f) for f in csv_files
            ]
    return datasets
