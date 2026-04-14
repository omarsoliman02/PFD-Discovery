"""Module d'evaluation et comparaison des approches.

Compare l'approche classique avec les workflows agentiques
sur les metriques : nombre de PFDs, qualite, temps d'execution.
"""

import json
import os
from datetime import datetime
from .validation import PFDResult


def compute_metrics(results: dict, approach_name: str) -> dict:
    """Calcule les metriques d'evaluation pour une approche."""
    pfds = results.get("generalized", results.get("pfds", []))

    avg_confidence = (
        sum(p.confidence for p in pfds) / len(pfds) if pfds else 0.0
    )
    avg_support = (
        sum(p.support for p in pfds) / len(pfds) if pfds else 0
    )
    max_confidence = max((p.confidence for p in pfds), default=0.0)
    min_confidence = min((p.confidence for p in pfds), default=0.0)

    # PFDs avec confidence parfaite
    perfect = [p for p in pfds if p.confidence == 1.0]
    # PFDs "interessantes" (pas identity triviale)
    interesting = [
        p for p in pfds
        if p.x_transformation.name != "identity"
    ]

    return {
        "approach": approach_name,
        "num_pfds": len(pfds),
        "num_perfect": len(perfect),
        "num_interesting": len(interesting),
        "avg_confidence": round(avg_confidence, 4),
        "avg_support": round(avg_support, 1),
        "max_confidence": round(max_confidence, 4),
        "min_confidence": round(min_confidence, 4),
        "num_candidates_explored": results.get("num_candidates", 0),
        "execution_time": round(results.get("execution_time", 0), 2),
    }


def compare_approaches(results_list: list[tuple[str, dict]]) -> str:
    """Compare plusieurs approches et retourne un tableau formate.

    Args:
        results_list: Liste de (nom_approche, resultats)

    Returns:
        Tableau comparatif formate en texte
    """
    metrics_list = []
    for name, results in results_list:
        metrics = compute_metrics(results, name)
        metrics_list.append(metrics)

    # Header
    headers = [
        "Approche", "PFDs", "Parfaites", "Interessantes",
        "Conf. moy.", "Support moy.", "Candidats", "Temps (s)"
    ]
    sep = "-" * 120

    lines = [sep]
    lines.append(
        f"{'Approche':<35} {'PFDs':>6} {'Parfaites':>10} {'Interes.':>10} "
        f"{'Conf.moy':>10} {'Supp.moy':>10} {'Candidats':>10} {'Temps(s)':>10}"
    )
    lines.append(sep)

    for m in metrics_list:
        lines.append(
            f"{m['approach']:<35} {m['num_pfds']:>6} {m['num_perfect']:>10} "
            f"{m['num_interesting']:>10} {m['avg_confidence']:>10.4f} "
            f"{m['avg_support']:>10.1f} {m['num_candidates_explored']:>10} "
            f"{m['execution_time']:>10.2f}"
        )

    lines.append(sep)
    return "\n".join(lines)


def save_results(results: dict, approach_name: str, dataset_name: str, output_dir: str = "results"):
    """Sauvegarde les resultats en JSON."""
    os.makedirs(output_dir, exist_ok=True)

    # Convertir les PFDResult en dicts serialisables
    serializable = {
        "approach": approach_name,
        "dataset": dataset_name,
        "timestamp": datetime.now().isoformat(),
        "num_candidates": results.get("num_candidates", 0),
        "num_valid": results.get("num_valid", 0),
        "num_generalized": results.get("num_generalized", 0),
        "execution_time": results.get("execution_time", 0),
        "llm_name": results.get("llm_name", "N/A"),
        "pfds": [
            {
                "rule": str(p),
                "x_transformation": str(p.x_transformation),
                "y_column": p.y_column,
                "support": p.support,
                "confidence": p.confidence,
                "noise": p.noise,
                "num_groups": p.num_groups,
            }
            for p in results.get("generalized", results.get("pfds", []))
        ],
        "agent_suggestions": results.get("agent_suggestions", []),
        "agent_transformations": results.get("agent_transformations", []),
        "prioritized_candidates": results.get("prioritized_candidates", []),
    }

    filename = f"{approach_name}_{dataset_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2, ensure_ascii=False)

    return filepath
