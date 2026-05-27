"""Module de generalisation de patterns.

Fusionne les PFDs specifiques en regles plus generales.
Exemple : "John*" -> M et "James*" -> M  =>  first_token(name) -> gender

Deux strategies disponibles :
  - generalize_pfds : algorithmique (preferre court prefix, subsomption identity)
  - generalize_pfds_llm : semantique via LLM (regroupe par concept metier)
"""

from .validation import PFDResult
from .pattern_extraction import Transformation


def generalize_pfds(pfds: list[PFDResult]) -> list[PFDResult]:
    """Generalise les PFDs en eliminant les redondances.

    Strategies :
    1. Si prefix(col, k) -> Y et prefix(col, k-1) -> Y avec des confidences proches,
       on garde la version plus courte (plus generale)
    2. Si identity(col) -> Y a une bonne confidence, elle subsume les transformations
       sur la meme colonne
    3. On elimine les doublons de meme colonne source et cible

    Returns:
        Liste de PFDs generalisees et dedupliquees
    """
    if not pfds:
        return []

    # Grouper par (colonne_source, colonne_cible)
    grouped: dict[tuple[str, str], list[PFDResult]] = {}
    for pfd in pfds:
        key = (pfd.x_transformation.column, pfd.y_column)
        grouped.setdefault(key, []).append(pfd)

    generalized = []

    for (src_col, tgt_col), group in grouped.items():
        # Trier par confidence decroissante puis support decroissant
        group.sort(key=lambda p: (p.confidence, p.support), reverse=True)

        # Strategie 1 : parmi les prefixes, garder le plus court avec bonne confidence
        prefix_pfds = [
            p for p in group if p.x_transformation.name == "prefix"
        ]
        other_pfds = [
            p for p in group if p.x_transformation.name != "prefix"
        ]

        if prefix_pfds:
            # Trier par longueur de prefix croissante
            prefix_pfds.sort(key=lambda p: p.x_transformation.params.get("k", 0))
            best_prefix = None
            for p in prefix_pfds:
                if best_prefix is None:
                    best_prefix = p
                elif p.confidence >= best_prefix.confidence - 0.05:
                    # Le prefix plus long n'apporte pas assez de gain
                    pass
                else:
                    best_prefix = p
            generalized.append(best_prefix)

        # Garder le meilleur parmi les numeric_prefix
        np_pfds = [p for p in other_pfds if p.x_transformation.name == "numeric_prefix"]
        non_np_pfds = [p for p in other_pfds if p.x_transformation.name != "numeric_prefix"]

        if np_pfds:
            np_pfds.sort(key=lambda p: p.x_transformation.params.get("k", 0))
            best_np = None
            for p in np_pfds:
                if best_np is None:
                    best_np = p
                elif p.confidence >= best_np.confidence - 0.05:
                    pass
                else:
                    best_np = p
            generalized.append(best_np)

        # Strategie 2 : pour identity et tokens, garder le meilleur par type
        seen_types = set()
        for p in non_np_pfds:
            t_name = p.x_transformation.name
            if t_name not in seen_types:
                generalized.append(p)
                seen_types.add(t_name)

    # Trier par confidence decroissante
    generalized.sort(key=lambda p: (p.confidence, p.support), reverse=True)
    return generalized


def generalize_pfds_llm(
    pfds: list[PFDResult],
    schema_info: dict,
    llm_name: str = "mistral",
    api_key: str | None = None,
    verbose: bool = False,
) -> tuple[list[PFDResult], list[dict]]:
    """Generalisation semantique par LLM.

    Demande au LLM de regrouper les PFDs par concept metier et de choisir
    une regle representante pour chaque groupe.

    Args:
        pfds: liste des PFDs validees
        schema_info: schema du dataset
        llm_name: nom du LLM a utiliser

    Returns:
        (pfds_generalisees, groupes_semantiques)
        pfds_generalisees : liste de PFDResult choisis comme representants
        groupes_semantiques : liste de dicts {concept, representative, members}
    """
    from .llm_agent import semantic_generalize

    if not pfds:
        return [], []

    # Construire la liste des PFDs sous forme de strings courtes
    pfd_strings = [
        f"{p.x_transformation} -> {p.y_column} [support={p.support}, conf={p.confidence:.3f}]"
        for p in pfds
    ]

    if verbose:
        print(f"[GEN-LLM] Demande de regroupement semantique a {llm_name} pour {len(pfds)} PFDs...")
    groups = semantic_generalize(pfd_strings, schema_info, llm_name, api_key)

    # Index par signature "transformation -> y_column"
    pfd_index: dict[str, PFDResult] = {}
    for p in pfds:
        sig = f"{p.x_transformation} -> {p.y_column}"
        pfd_index[sig] = p

    # Pour chaque groupe, retrouver la regle representante
    representatives: list[PFDResult] = []
    used_signatures: set[str] = set()

    for g in groups:
        rep_str = g.get("representative", "")
        # Strip support/conf si presents
        rep_sig = rep_str.split(" [")[0].strip()
        if rep_sig in pfd_index and rep_sig not in used_signatures:
            representatives.append(pfd_index[rep_sig])
            used_signatures.add(rep_sig)
            # Marquer les membres comme deja regroupes
            for m in g.get("members", []):
                m_sig = m.split(" [")[0].strip()
                used_signatures.add(m_sig)

    # PFDs qui n'ont ete classees dans aucun groupe -> on les garde aussi
    for sig, p in pfd_index.items():
        if sig not in used_signatures:
            representatives.append(p)

    representatives.sort(key=lambda p: (p.confidence, p.support), reverse=True)
    if verbose:
        print(f"[GEN-LLM] {len(groups)} groupes formes, {len(representatives)} regles representantes")

    return representatives, groups
