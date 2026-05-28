"""Module d'integration LLM pour la decouverte agentique de PFDs.

Utilise des modeles locaux via Ollama (zero quota, gratuit, offline) :
  - Mistral 7B
  - Llama 3.1 8B

Chaque agent peut :
  1. Suggerer des transformations pertinentes (Workflow 1)
  2. Prioriser des candidats X -> Y (Workflow 2)
"""

import json
import re
import urllib.request


TRANSFORMATION_SUGGESTION_PROMPT = """Tu es un expert en qualite de donnees et decouverte de dependances fonctionnelles.

On te donne un dataset avec les colonnes et echantillons de valeurs suivants :

{schema_info}

Ta tache : Suggerer des transformations pertinentes a appliquer sur les colonnes pour decouvrir des Pattern Functional Dependencies (PFDs).

Les transformations disponibles sont :
- prefix(colonne, k) : les k premiers caracteres (utile pour codes postaux, numeros de telephone, etc.)
- suffix(colonne, k) : les k derniers caracteres
- first_token(colonne) : le premier mot (utile pour noms de personnes => prenom)
- last_token(colonne) : le dernier mot
- numeric_prefix(colonne, k) : les k premiers chiffres
- identity(colonne) : la valeur brute (utile quand la colonne a des valeurs categoriques)
- length(colonne) : la longueur de la chaine

Pour chaque transformation suggeree, explique pourquoi elle est pertinente.

Reponds UNIQUEMENT en JSON avec ce format exact :
{{
  "transformations": [
    {{
      "name": "prefix",
      "column": "ZIP",
      "params": {{"k": 3}},
      "reason": "Les 3 premiers chiffres du code postal determinent souvent la ville"
    }}
  ]
}}
"""

CANDIDATE_PRIORITIZATION_PROMPT = """Tu es un expert en qualite de donnees et decouverte de dependances fonctionnelles.

On te donne un dataset avec les colonnes et echantillons de valeurs suivants :

{schema_info}

Et les transformations suivantes ont ete generees :
{transformations}

Ta tache : Parmi toutes les paires possibles (transformation_X -> colonne_Y), identifier les candidats les plus prometteurs pour decouvrir des Pattern Functional Dependencies (PFDs) significatives.

Une bonne PFD :
- A du sens semantique (ex: prefix(zip,3) -> city a du sens, first_token(name) -> city n'en a pas)
- Couvre un grand nombre de tuples (bon support)
- A une haute confidence (la plupart des tuples dans un groupe ont la meme valeur Y)

IMPORTANT : pour les colonnes categoriques avec peu de valeurs uniques (codes de departement, ID, abbreviations), n'oublie PAS de proposer la transformation identity(col) qui correspond aux Dependances Fonctionnelles classiques (souvent confidence = 1.0). Mais la colonne cible Y doit etre une AUTRE colonne (ex: identity(Department) -> Department Name).

REGLE ABSOLUE : x_transformation et y_column doivent porter sur des colonnes DIFFERENTES. Ne propose JAMAIS une regle triviale X -> X (ex: identity(Gender) -> Gender), elle n'a aucun interet.

Reponds UNIQUEMENT en JSON avec ce format exact :
{{
  "candidates": [
    {{
      "x_transformation": "prefix(ZIP, 3)",
      "y_column": "CITY",
      "priority": "high",
      "reason": "Les 3 premiers chiffres du code postal determinent generalement la ville"
    }}
  ]
}}

Classe les candidats par priorite : "high", "medium", "low".
Ne propose que les candidats qui ont du sens semantiquement. Evite les candidats triviaux ou absurdes.
"""


# ============================================================
# WORKFLOW 3 : Agent-in-the-Loop
# ============================================================

INITIAL_HYPOTHESIS_PROMPT = """Tu es un expert en qualite de donnees et decouverte de Pattern Functional Dependencies (PFDs).

On te donne un dataset avec les colonnes EXACTES suivantes :

{schema_info}

REGLE CRITIQUE : tu DOIS utiliser EXACTEMENT les noms de colonnes ci-dessus (case-sensitive, espaces compris). N'invente JAMAIS de nouvelle colonne. Si tu n'es pas sur, recopie le nom mot pour mot.

Ta tache : proposer une LISTE INITIALE D'HYPOTHESES de PFDs candidates.

Une PFD a la forme : transformation(X) -> Y, ou X et Y sont parmi les colonnes ci-dessus, et transformation est l'une parmi :
- identity(col) : valeur brute (pour colonnes categoriques)
- prefix(col, k) : k premiers caracteres
- suffix(col, k) : k derniers caracteres
- first_token(col) : premier mot
- last_token(col) : dernier mot
- numeric_prefix(col, k) : k premiers chiffres
- length(col) : longueur

Propose 4 a 8 hypotheses qui semblent semantiquement pertinentes. X et Y DOIVENT etre des colonnes existantes (recopiees du schema ci-dessus) et DIFFERENTES l'une de l'autre (jamais X -> X, ex: identity(Gender) -> Gender est interdit).

Reponds UNIQUEMENT en JSON :
{{
  "hypotheses": [
    {{
      "x_transformation": "identity(NOM_EXACT_DE_COLONNE)",
      "y_column": "NOM_EXACT_AUTRE_COLONNE",
      "rationale": "Pourquoi cette regle a du sens"
    }}
  ]
}}
"""


REFINEMENT_PROMPT = """Tu es un expert en qualite de donnees. Tu es en train d'iterer sur la decouverte de PFDs.

Schema du dataset :
{schema_info}

A l'iteration precedente, tu avais propose ces hypotheses. L'algorithme les a validees et renvoie le feedback ci-dessous :

REGLES FORTES (a CONSERVER, confidence >= {min_confidence}) :
{strong_rules}

REGLES FAIBLES (a RAFFINER, confidence < {min_confidence}) :
{weak_rules}

REGLES REJETEES (support trop bas, < {min_support}) :
{rejected_rules}

Ta tache de raffinement :
1. Pour chaque REGLE FAIBLE, propose une ALTERNATIVE plus stricte. Exemples :
   - Si prefix(ZIP, 2) -> city a conf=0.6, essaye prefix(ZIP, 3) ou prefix(ZIP, 4)
   - Si first_token(Name) -> Gender a conf=0.7, essaye prefix(Name, 1) ou identity(Name)
   - Si une regle echoue completement, abandonne-la
2. Propose 1 ou 2 NOUVELLES HYPOTHESES sur des paires (X, Y) que tu n'avais pas encore testees.
3. Reconserve les regles fortes uniquement si tu veux les retester (sinon ne les inclus pas).

Reponds UNIQUEMENT en JSON :
{{
  "refinements": [
    {{
      "x_transformation": "prefix(ZIP, 3)",
      "y_column": "city",
      "rationale": "Raffinement de prefix(ZIP, 2) qui avait conf=0.6 -- essayons k=3",
      "replaces": "prefix(ZIP, 2) -> city"
    }}
  ],
  "new_hypotheses": [
    {{
      "x_transformation": "domain(email)",
      "y_column": "organization",
      "rationale": "Le domaine d'email determine souvent l'organisation"
    }}
  ]
}}
"""


# ============================================================
# GENERALISATION SEMANTIQUE (etape 5 LLM-aware)
# ============================================================

SEMANTIC_GENERALIZATION_PROMPT = """Tu es un expert en qualite de donnees. On a decouvert les PFDs suivantes sur un dataset :

{pfds_list}

Schema du dataset :
{schema_info}

Ta tache : REGROUPER ces PFDs en CONCEPTS METIER plus generaux quand elles capturent la meme idee semantique.

Exemple :
- "prefix(Name, 1) -> Gender" et "first_token(Name) -> Gender" et "identity(Name) -> Gender" expriment toutes le concept : "Le prenom determine le genre"
- On les regroupe sous une regle conceptuelle unique.

Pour chaque groupe, choisis la regle REPRESENTANTE (celle qui generalise le mieux : prefere first_token > prefix > identity quand possible, et prefere le prefix le plus court a confidence egale).

Les regles qui n'ont pas d'equivalent semantique restent seules (groupe d'une regle).

Reponds UNIQUEMENT en JSON :
{{
  "groups": [
    {{
      "concept": "Le prenom determine le genre",
      "representative": "first_token(Name) -> Gender",
      "members": ["prefix(Name, 1) -> Gender", "first_token(Name) -> Gender"]
    }},
    {{
      "concept": "Le code de departement determine le nom du departement",
      "representative": "identity(Department) -> Department Name",
      "members": ["identity(Department) -> Department Name"]
    }}
  ]
}}
"""


def format_schema_for_prompt(schema_info: dict) -> str:
    """Formate les infos de schema pour insertion dans un prompt LLM."""
    lines = []
    for col, info in schema_info.items():
        samples = ", ".join(f'"{v}"' for v in info["sample_values"][:5])
        lines.append(
            f"- {col} ({info['num_unique']} valeurs uniques sur {info['num_rows']} lignes) : "
            f"exemples = [{samples}]"
        )
    return "\n".join(lines)


# ============================================================
# OLLAMA -- Modeles locaux (sans limite)
# ============================================================

OLLAMA_BASE_URL = "http://localhost:11434"


def call_ollama(prompt: str, model: str, base_url: str = OLLAMA_BASE_URL) -> str:
    """Appelle un modele local via Ollama REST API.

    Args:
        prompt: Le prompt a envoyer
        model: Nom du modele Ollama (ex: "mistral", "llama3.1")
        base_url: URL du serveur Ollama
    """
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 4096,
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{base_url}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    with urllib.request.urlopen(req, timeout=600) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        return result.get("response", "")


def call_mistral(prompt: str, api_key: str | None = None) -> str:
    """Appelle Mistral 7B via Ollama (local, sans quota)."""
    return call_ollama(prompt, model="mistral")


def call_llama(prompt: str, api_key: str | None = None) -> str:
    """Appelle Llama 3.1 8B via Ollama (local, sans quota)."""
    return call_ollama(prompt, model="llama3.1")


# ============================================================
# DISPATCHER
# ============================================================

LLM_REGISTRY = {
    "mistral": call_mistral,
    "llama": call_llama,
}


def call_llm(prompt: str, llm_name: str = "mistral", api_key: str | None = None) -> str:
    """Appelle un LLM par son nom.

    Modeles disponibles (locaux via Ollama) : "mistral", "llama"
    """
    if llm_name not in LLM_REGISTRY:
        available = ", ".join(LLM_REGISTRY.keys())
        raise ValueError(f"LLM inconnu: {llm_name}. Disponibles: {available}")

    return LLM_REGISTRY[llm_name](prompt, api_key)


def parse_json_response(response: str) -> dict:
    """Extrait et parse le JSON d'une reponse LLM."""
    json_match = re.search(r'\{[\s\S]*\}', response)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return {"error": "Impossible de parser le JSON", "raw": response}


def suggest_transformations(
    schema_info: dict,
    llm_name: str = "mistral",
    api_key: str | None = None,
) -> list[dict]:
    """Demande au LLM de suggerer des transformations pertinentes.

    Returns:
        Liste de dicts avec {name, column, params, reason}
    """
    schema_text = format_schema_for_prompt(schema_info)
    prompt = TRANSFORMATION_SUGGESTION_PROMPT.format(schema_info=schema_text)

    response = call_llm(prompt, llm_name, api_key)
    parsed = parse_json_response(response)

    return parsed.get("transformations", [])


def prioritize_candidates(
    schema_info: dict,
    transformations_str: list[str],
    llm_name: str = "mistral",
    api_key: str | None = None,
) -> list[dict]:
    """Demande au LLM de prioriser les candidats X -> Y.

    Returns:
        Liste de dicts avec {x_transformation, y_column, priority, reason}
    """
    schema_text = format_schema_for_prompt(schema_info)
    transf_text = "\n".join(f"- {t}" for t in transformations_str)
    prompt = CANDIDATE_PRIORITIZATION_PROMPT.format(
        schema_info=schema_text,
        transformations=transf_text,
    )

    response = call_llm(prompt, llm_name, api_key)
    parsed = parse_json_response(response)

    return parsed.get("candidates", [])


def propose_initial_hypotheses(
    schema_info: dict,
    llm_name: str = "mistral",
    api_key: str | None = None,
) -> list[dict]:
    """Demande au LLM de proposer les hypotheses initiales de PFDs (Workflow 3).

    Returns:
        Liste de dicts {x_transformation, y_column, rationale}
    """
    schema_text = format_schema_for_prompt(schema_info)
    prompt = INITIAL_HYPOTHESIS_PROMPT.format(schema_info=schema_text)
    response = call_llm(prompt, llm_name, api_key)
    parsed = parse_json_response(response)
    return parsed.get("hypotheses", [])


def refine_hypotheses(
    schema_info: dict,
    strong_rules: list[dict],
    weak_rules: list[dict],
    rejected_rules: list[dict],
    min_support: int,
    min_confidence: float,
    llm_name: str = "mistral",
    api_key: str | None = None,
) -> dict:
    """Demande au LLM de raffiner les hypotheses apres feedback algorithmique.

    Args:
        strong_rules: regles avec conf >= min_confidence
        weak_rules: regles validees mais conf < min_confidence
        rejected_rules: regles avec support < min_support
        min_support, min_confidence: seuils

    Returns:
        Dict {refinements: [...], new_hypotheses: [...]}
    """
    def _fmt(rules):
        if not rules:
            return "  (aucune)"
        lines = []
        for r in rules:
            line = f"  - {r['x_transformation']} -> {r['y_column']} [support={r['support']}, conf={r['confidence']:.3f}]"
            lines.append(line)
        return "\n".join(lines)

    schema_text = format_schema_for_prompt(schema_info)
    prompt = REFINEMENT_PROMPT.format(
        schema_info=schema_text,
        strong_rules=_fmt(strong_rules),
        weak_rules=_fmt(weak_rules),
        rejected_rules=_fmt(rejected_rules),
        min_support=min_support,
        min_confidence=min_confidence,
    )
    response = call_llm(prompt, llm_name, api_key)
    parsed = parse_json_response(response)
    return {
        "refinements": parsed.get("refinements", []),
        "new_hypotheses": parsed.get("new_hypotheses", []),
    }


def semantic_generalize(
    pfds_str_list: list[str],
    schema_info: dict,
    llm_name: str = "mistral",
    api_key: str | None = None,
) -> list[dict]:
    """Demande au LLM de regrouper semantiquement les PFDs decouvertes.

    Args:
        pfds_str_list: liste de PFDs sous forme "transformation -> Y [support=X, conf=Y]"
        schema_info: schema du dataset

    Returns:
        Liste de groupes {concept, representative, members}
    """
    schema_text = format_schema_for_prompt(schema_info)
    pfds_text = "\n".join(f"- {p}" for p in pfds_str_list)
    prompt = SEMANTIC_GENERALIZATION_PROMPT.format(
        pfds_list=pfds_text,
        schema_info=schema_text,
    )
    response = call_llm(prompt, llm_name, api_key)
    parsed = parse_json_response(response)
    return parsed.get("groups", [])
