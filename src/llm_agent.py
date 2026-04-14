"""Module d'integration LLM pour la decouverte agentique de PFDs.

Supporte deux LLMs :
  - Claude (Anthropic)
  - Gemini (Google)

Chaque agent peut :
  1. Suggerer des transformations pertinentes (Workflow 1)
  2. Prioriser des candidats X -> Y (Workflow 2)
"""

import os
import json
import re


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


def call_claude(prompt: str, api_key: str | None = None) -> str:
    """Appelle l'API Claude et retourne la reponse."""
    import anthropic

    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY non definie")

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def call_gemini(prompt: str, api_key: str | None = None) -> str:
    """Appelle l'API Gemini et retourne la reponse."""
    from google import genai

    api_key = api_key or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY non definie")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    return response.text


def call_llm(prompt: str, llm_name: str = "claude", api_key: str | None = None) -> str:
    """Appelle un LLM par son nom."""
    if llm_name == "claude":
        return call_claude(prompt, api_key)
    elif llm_name == "gemini":
        return call_gemini(prompt, api_key)
    else:
        raise ValueError(f"LLM inconnu: {llm_name}")


def parse_json_response(response: str) -> dict:
    """Extrait et parse le JSON d'une reponse LLM."""
    # Chercher un bloc JSON dans la reponse
    json_match = re.search(r'\{[\s\S]*\}', response)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    # Essayer la reponse entiere
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return {"error": "Impossible de parser le JSON", "raw": response}


def suggest_transformations(
    schema_info: dict,
    llm_name: str = "claude",
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
    llm_name: str = "claude",
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
