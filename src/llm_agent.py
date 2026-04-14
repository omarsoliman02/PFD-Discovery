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

    with urllib.request.urlopen(req, timeout=300) as resp:
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
